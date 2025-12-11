from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()
from study_buddy import get_question_crew, get_grading_crew
from servicenow_tools import get_instance_stats, get_applications, get_recent_errors, get_security_stats, get_integration_health
from admin_agent import run_admin_command, analyze_error_log

app = Flask(__name__)
# ... (existing code) ...

@app.route('/security_stats', methods=['GET'])
def security_stats():
    try:
        stats = get_security_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/integration_stats', methods=['GET'])
def integration_stats():
    try:
        stats = get_integration_health()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/errors', methods=['GET'])
def errors():
    try:
        errs = get_recent_errors()
        return jsonify(errs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyze_error', methods=['POST'])
def analyze_error():
    data = request.json
    msg = data.get('message')
    if not msg:
        return jsonify({"error": "Message required"}), 400
    try:
        analysis = analyze_error_log(msg)
        return jsonify({"analysis": analysis})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
CORS(app)

@app.route('/start_interview', methods=['POST'])
def start_interview():
    data = request.json
    topic = data.get('topic')
    if not topic:
        return jsonify({"error": "Topic is required"}), 400
    
    try:
        # This runs the research and returns the question
        question = get_question_crew(topic)
        return jsonify({"question": question})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = request.json
    topic = data.get('topic')
    question = data.get('question')
    answer = data.get('answer')
    
    if not all([topic, question, answer]):
        return jsonify({"error": "Missing fields"}), 400
        
    try:
        grade = get_grading_crew(topic, question, answer)
        return jsonify({"grade": grade})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin_command', methods=['POST'])
def admin_command():
    data = request.json
    command = data.get('command')
    history = data.get('history', []) # Get history from frontend
    
    if not command:
        return jsonify({"error": "Command is required"}), 400
    
    try:
        result = run_admin_command(command, history)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/instance_stats', methods=['GET'])
def instance_stats():
    try:
        stats = get_instance_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/applications', methods=['GET'])
def applications():
    try:
        apps = get_applications()
        return jsonify(apps)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)
