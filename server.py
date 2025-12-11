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
    url = request.args.get('instance_url')
    if not url: return jsonify({"error": "Instance URL required"}), 400
    try:
        stats = get_security_stats(url)
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/integration_stats', methods=['GET'])
def integration_stats():
    url = request.args.get('instance_url')
    if not url: return jsonify({"error": "Instance URL required"}), 400
    try:
        stats = get_integration_health(url)
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/errors', methods=['GET'])
def errors():
    url = request.args.get('instance_url')
    if not url: return jsonify({"error": "Instance URL required"}), 400
    try:
        errs = get_recent_errors(url)
        return jsonify(errs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyze_error', methods=['POST'])
def analyze_error():
    data = request.json
    msg = data.get('message')
    url = data.get('instance_url')
    if not msg or not url:
        return jsonify({"error": "Message and Instance URL required"}), 400
    try:
        analysis = analyze_error_log(msg, url)
        return jsonify({"analysis": analysis})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
CORS(app)

@app.route('/start_interview', methods=['POST'])
def start_interview():
    data = request.json
    topic = data.get('topic')
    url = data.get('instance_url')
    if not topic or not url:
        return jsonify({"error": "Topic and Instance URL required"}), 400
    
    try:
        # This runs the research and returns the question
        question = get_question_crew(topic, url)
        return jsonify({"question": question})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = request.json
    topic = data.get('topic')
    question = data.get('question')
    answer = data.get('answer')
    url = data.get('instance_url')
    
    if not all([topic, question, answer, url]):
        return jsonify({"error": "Missing fields (topic, question, answer, instance_url)"}), 400
        
    try:
        grade = get_grading_crew(topic, question, answer, url)
        return jsonify({"grade": grade})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin_command', methods=['POST'])
def admin_command():
    data = request.json
    command = data.get('command')
    history = data.get('history', []) # Get history from frontend
    url = data.get('instance_url')
    
    if not command or not url:
        return jsonify({"error": "Command and Instance URL required"}), 400
    
    try:
        result = run_admin_command(command, url, history)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/instance_stats', methods=['GET'])
def instance_stats():
    url = request.args.get('instance_url')
    if not url: return jsonify({"error": "Instance URL required"}), 400
    try:
        stats = get_instance_stats(url)
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/applications', methods=['GET'])
def applications():
    url = request.args.get('instance_url')
    if not url: return jsonify({"error": "Instance URL required"}), 400
    try:
        apps = get_applications(url)
        return jsonify(apps)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5001, debug=True)
