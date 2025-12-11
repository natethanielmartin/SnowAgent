import signal
import sys

# Windows compatibility fix for crewai
if sys.platform == "win32":
    # Mock missing signals on Windows
    for sig in ['SIGHUP', 'SIGTSTP', 'SIGQUIT', 'SIGCONT', 'SIGUSR1', 'SIGUSR2', 'SIGPIPE', 'SIGALRM']:
        if not hasattr(signal, sig):
            setattr(signal, sig, 1)

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()
from servicenow_tools import get_instance_stats, get_applications, get_recent_errors, get_security_stats, get_integration_health, check_connection, get_records
from admin_agent import run_admin_command, analyze_error_log

app = Flask(__name__)
CORS(app)
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
    print(f"Received instance_stats request for: {url}")
    if not url: return jsonify({"error": "Instance URL required"}), 400
    try:
        print("Calling get_instance_stats...")
        stats = get_instance_stats(url)
        print(f"get_instance_stats returned: {stats}")
        return jsonify(stats)
    except Exception as e:
        print(f"instance_stats error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/test_connection', methods=['POST'])
def test_connection():
    data = request.json
    url = data.get('instance_url')
    if not url: return jsonify({"error": "Instance URL required"}), 400
    
    print(f"Testing connection to: {url}")
    result = check_connection(url)
    print(f"Connection result: {result}")
    return jsonify(result)

@app.route('/applications', methods=['GET'])
def applications():
    url = request.args.get('instance_url')
    if not url: return jsonify({"error": "Instance URL required"}), 400
    try:
        apps = get_applications(url)
        return jsonify(apps)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/records', methods=['POST'])
def records():
    data = request.json
    url = data.get('instance_url')
    table = data.get('table')
    query = data.get('query')
    limit = data.get('limit', 20)
    fields = data.get('fields')

    if not url or not table or not query:
        return jsonify({"error": "Instance URL, Table, and Query required"}), 400
    
    try:
        records = get_records(url, table, query, fields, limit)
        return jsonify(records)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5001, debug=True)
