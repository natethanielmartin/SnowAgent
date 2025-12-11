import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from servicenow_tools import ServiceNowQueryTool, ServiceNowCreateTool, ServiceNowUpdateTool

load_dotenv()

# --- CONFIGURATION ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- LLM SETUP ---
gemini_llm = LLM(
    model="openai/gemini-flash-latest",
    api_key=GOOGLE_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    temperature=0.7
)

def get_agent(instance_url):
    query_tool = ServiceNowQueryTool(instance_url=instance_url)
    create_tool = ServiceNowCreateTool(instance_url=instance_url)
    update_tool = ServiceNowUpdateTool(instance_url=instance_url)

    return Agent(
        role='ServiceNow System Administrator',
        goal='Execute administrative tasks in ServiceNow based on user requests.',
        backstory="""You are an expert ServiceNow Administrator. 
        You know the internal table names (e.g., 'sys_user', 'incident', 'sys_script_client', 'sys_scope').
        You are careful when creating or updating records.
        You always verify table names before acting.""",
        tools=[query_tool, create_tool, update_tool],
        llm=gemini_llm,
        verbose=True
    )

# --- FUNCTION FOR API ---
def run_admin_command(user_request, instance_url, history=[]):
    # Format history for the agent
    history_str = ""
    for msg in history:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        history_str += f"{role.upper()}: {content}\n"

    agent = get_agent(instance_url)

    task_admin = Task(
        description=f"""
        Current User Request: "{user_request}"
        
        Conversation History:
        {history_str}
        
        INSTRUCTIONS:
        1. Analyze the request and history.
        2. If the user's intent is ambiguous (e.g., "create a ticket" could be Incident, Change, or Problem), DO NOT GUESS.
           Instead, return a response asking the user to clarify (e.g., "Did you mean an Incident or a Change Request?").
           You can also list options for them to choose from.
        3. If the request is clear (e.g., "Create an Incident"), identify the table and fields.
        4. Use the appropriate tool (Query, Create, Update) ONLY when you are sure.
        
        If creating a record, generate realistic dummy data for required fields ONLY if the user hasn't specified them.
        """,
        expected_output='If asking a question: The question text. If executing an action: A summary of the action and result.',
        agent=agent
    )

    crew = Crew(
        agents=[agent],
        tasks=[task_admin],
        process=Process.sequential,
        verbose=True
    )

    result = crew.kickoff()
    return str(result)

def analyze_error_log(error_message, instance_url):
    agent = get_agent(instance_url)

    task_analysis = Task(
        description=f"""
        Analyze the following ServiceNow Error Log:
        "{error_message}"
        
        1. Explain what this error means in plain English.
        2. Identify the likely root cause (e.g., syntax error, missing ACL, null pointer).
        3. Provide a specific fix or troubleshooting step.
        """,
        expected_output='A concise analysis with a "Root Cause" and "Suggested Fix" section.',
        agent=agent
    )

    crew = Crew(
        agents=[agent],
        tasks=[task_analysis],
        process=Process.sequential,
        verbose=True
    )

    result = crew.kickoff()
    return str(result)

# --- CLI RUNNER ---
if __name__ == "__main__":
    print("🛠️ ServiceNow Admin Agent is ready.")
    print("Examples:")
    print(" - 'Find the user with email admin@example.com'")
    print(" - 'Create a P1 incident for a Server Outage'")
    print(" - 'List the last 3 created Business Rules'")
    
    user_request = input("\nWhat would you like to do? ")
    print(run_admin_command(user_request))
