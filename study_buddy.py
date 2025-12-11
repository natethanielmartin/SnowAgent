import os
import requests
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool

load_dotenv()

# --- CONFIGURATION ---
INSTANCE_URL = "https://dev309858.service-now.com"
USERNAME = os.getenv("SN_USERNAME")
PASSWORD = os.getenv("SN_PASSWORD") 
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- GEMINI SETUP (Trojan Horse via LLM class) ---
# We use CrewAI's LLM class, but configure it to use OpenAI provider pointing to Google.
gemini_llm = LLM(
    model="openai/gemini-flash-latest",
    api_key=GOOGLE_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    temperature=0.7
)

# --- 1. DEFINE THE TOOL ---
class ServiceNowKnowledgeTool(BaseTool):
    name: str = "ServiceNow Knowledge Search"
    description: str = "Searches the ServiceNow Knowledge Base for technical articles."

    def _run(self, query: str) -> str:
        url = f"{INSTANCE_URL}/api/now/table/kb_knowledge"
        params = {
            'sysparm_query': f'short_descriptionLIKE{query}^workflow_state=published',
            'sysparm_limit': 3, 
            'sysparm_fields': 'short_description,text,number'
        }
        
        try:
            response = requests.get(
                url, 
                auth=(USERNAME, PASSWORD), 
                headers={"Content-Type": "application/json"}, 
                params=params
            )
            
            if response.status_code == 200:
                results = response.json().get('result', [])
                if not results:
                    return "No articles found."
                return "\n\n".join([f"Article {r['number']}: {r['short_description']}\nContent: {r['text'][:800]}..." for r in results])
            else:
                return f"Error fetching data: {response.status_code}"
        except Exception as e:
            return f"Connection Failed: {str(e)}"

sn_tool = ServiceNowKnowledgeTool()

# --- 2. DEFINE THE AGENTS ---

researcher = Agent(
    role='ServiceNow Technical Researcher',
    goal='Find accurate technical documentation on {topic}',
    backstory='You are a specialist in navigating ServiceNow documentation.',
    tools=[sn_tool],
    llm=gemini_llm, 
    verbose=True
)

interviewer = Agent(
    role='Senior ServiceNow Architect',
    goal='Quiz the user on {topic} based on retrieved documentation.',
    backstory='You are a strict technical interviewer. You ask scenario-based questions.',
    llm=gemini_llm, 
    verbose=True
)

# --- 4. MODULAR FUNCTIONS FOR API ---

def get_question_crew(topic):
    """
    Phase 1: Research the topic and generate an interview question.
    Returns: { "question": str, "context": str }
    """
    # Task 1: Research
    task_research = Task(
        description=f'Search the Knowledge Base for: {topic}. Summarize technical facts.',
        expected_output='A bulleted list of technical facts.',
        agent=researcher
    )

    # Task 2: Generate Question (No human input here, just generation)
    task_generate_question = Task(
        description=f'Based on the research about {topic}, formulate a challenging interview question. Output ONLY the question.',
        expected_output='The interview question.',
        agent=interviewer
    )

    crew = Crew(
        agents=[researcher, interviewer],
        tasks=[task_research, task_generate_question],
        process=Process.sequential,
        verbose=True
    )

    result = crew.kickoff()
    
    # We need to extract the "Context" (Research) to pass to the next step.
    # In a real app, we might store this in a DB. For now, we'll try to return the raw output.
    # CrewAI returns the final task output by default.
    return str(result)

def get_grading_crew(topic, question, answer):
    """
    Phase 2: Grade the user's answer.
    """
    # Task: Grade
    task_grade = Task(
        description=f"""
        Topic: {topic}
        Question: {question}
        User Answer: {answer}
        
        Grade the user's answer based on technical accuracy regarding ServiceNow.
        Provide a Pass/Fail grade and detailed feedback.
        """,
        expected_output='Pass/Fail grade with feedback.',
        agent=interviewer
    )

    crew = Crew(
        agents=[interviewer],
        tasks=[task_grade],
        process=Process.sequential,
        verbose=True
    )

    result = crew.kickoff()
    return str(result)

# --- 5. CLI RUNNER ---
if __name__ == "__main__":
    print("🤖 Gemini Agent is starting (CLI Mode)...")
    topic_input = input("Topic: ")
    
    # Run Phase 1
    print("\n... Researching and Generating Question ...\n")
    question = get_question_crew(topic_input)
    print(f"\nINTERVIEWER: {question}\n")
    
    # Run Phase 2
    answer_input = input("Your Answer: ")
    print("\n... Grading ...\n")
    grade = get_grading_crew(topic_input, question, answer_input)
    print(f"\nREPORT CARD:\n{grade}")