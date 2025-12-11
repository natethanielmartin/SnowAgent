import requests
import json
import os
from dotenv import load_dotenv
from crewai.tools import BaseTool

load_dotenv()

# --- CONFIGURATION ---
INSTANCE_URL = "https://dev309858.service-now.com"
USERNAME = os.getenv("SN_USERNAME")
PASSWORD = os.getenv("SN_PASSWORD") 

def get_instance_stats():
    """
    Fetches aggregate counts for the dashboard.
    Returns dict with keys: incidents, users, jobs
    """
    stats = {
        "incidents": 0,
        "users": 0,
        "failed_jobs": 0,
        "p1_incidents": 0,
        "unassigned_incidents": 0,
        "active_changes": 0
    }
    
    headers = {"Content-Type": "application/json"}
    
    # helper for stats api
    def get_count(table, query):
        url = f"{INSTANCE_URL}/api/now/stats/{table}"
        params = {
            'sysparm_count': 'true',
            'sysparm_query': query
        }
        try:
            res = requests.get(url, auth=(USERNAME, PASSWORD), headers=headers, params=params)
            if res.status_code == 200:
                return res.json().get('result', {}).get('stats', {}).get('count', 0)
        except:
            pass
        return 0

    stats["incidents"] = get_count('incident', 'active=true')
    stats["users"] = get_count('sys_user', 'active=true')
    stats["failed_jobs"] = get_count('sys_trigger', 'state=3') # 3 = Error
    
    stats["p1_incidents"] = get_count('incident', 'active=true^priority=1')
    stats["unassigned_incidents"] = get_count('incident', 'active=true^assigned_toISEMPTY')
    stats["active_changes"] = get_count('change_request', 'active=true')

    # Learning Metrics
    # Errors = Level 2. created_onONToday... is a ServiceNow date constant
    stats["today_errors"] = get_count('syslog', 'level=2^sys_created_onONToday@javascript:gs.beginningOfToday()@javascript:gs.endOfToday()')
    stats["recent_updates"] = get_count('sys_update_xml', 'sys_created_onONToday@javascript:gs.beginningOfToday()@javascript:gs.endOfToday()')
    stats["total_business_rules"] = get_count('sys_script', 'active=true')
    
    return stats

def get_applications():
    """
    Fetches a list of applications from sys_scope.
    """
    url = f"{INSTANCE_URL}/api/now/table/sys_scope"
    params = {
        'sysparm_limit': 50,
        'sysparm_fields': 'name,scope,version,sys_updated_on',
        'sysparm_query': 'orderbydesc:sys_updated_on'
    }
    try:
        response = requests.get(
            url, 
            auth=(USERNAME, PASSWORD), 
            headers={"Content-Type": "application/json"}, 
            params=params
        )
        if response.status_code == 200:
            return response.json().get('result', [])
    except Exception:
        pass
    return []

def get_recent_errors(limit=10):
    """
    Fetches recent error logs from syslog.
    """
    url = f"{INSTANCE_URL}/api/now/table/syslog"
    params = {
        'sysparm_limit': limit,
        'sysparm_fields': 'sys_created_on,source,message,sys_id',
        'sysparm_query': 'level=2^orderbydesc:sys_created_on' # Level 2 = Error
    }
    try:
        response = requests.get(
            url, 
            auth=(USERNAME, PASSWORD), 
            headers={"Content-Type": "application/json"}, 
            params=params
        )
        if response.status_code == 200:
            return response.json().get('result', [])
    except Exception:
        pass
    return []

def get_security_stats():
    """
    Fetches security related stats.
    """
    headers = {"Content-Type": "application/json"}
    stats = {"failed_logins": 0, "new_admins": 0}

    # 1. Failed Logins Today (sysevent)
    url_events = f"{INSTANCE_URL}/api/now/stats/sysevent"
    params_events = {
        'sysparm_count': 'true',
        'sysparm_query': 'name=login.failed^sys_created_onONToday@javascript:gs.beginningOfToday()@javascript:gs.endOfToday()'
    }
    
    # 2. New Admin Roles Granted Today (sys_user_has_role)
    url_roles = f"{INSTANCE_URL}/api/now/stats/sys_user_has_role"
    params_roles = {
        'sysparm_count': 'true',
        'sysparm_query': 'role.name=admin^sys_created_onONToday@javascript:gs.beginningOfToday()@javascript:gs.endOfToday()'
    }

    try:
        # Fetch Events
        r1 = requests.get(url_events, auth=(USERNAME, PASSWORD), headers=headers, params=params_events)
        if r1.status_code == 200:
            stats["failed_logins"] = r1.json().get('result', {}).get('stats', {}).get('count', 0)
        
        # Fetch Roles
        r2 = requests.get(url_roles, auth=(USERNAME, PASSWORD), headers=headers, params=params_roles)
        if r2.status_code == 200:
            stats["new_admins"] = r2.json().get('result', {}).get('stats', {}).get('count', 0)

    except Exception:
        pass
        
    return stats

def get_integration_health():
    """
    Fetches integration health (ECC Queue).
    """
    headers = {"Content-Type": "application/json"}
    stats = {"ecc_errors": 0}

    # ECC Queue Errors Today
    url = f"{INSTANCE_URL}/api/now/stats/ecc_queue"
    params = {
        'sysparm_count': 'true',
        'sysparm_query': 'state=error^sys_created_onONToday@javascript:gs.beginningOfToday()@javascript:gs.endOfToday()'
    }
    
    try:
        r = requests.get(url, auth=(USERNAME, PASSWORD), headers=headers, params=params)
        if r.status_code == 200:
            stats["ecc_errors"] = r.json().get('result', {}).get('stats', {}).get('count', 0)
    except Exception:
        pass

    return stats

class ServiceNowQueryTool(BaseTool):
    name: str = "ServiceNow Table Query"
    description: str = "Queries any ServiceNow table. Useful for finding records (Users, Incidents, Scripts, etc). Input should be a pipe-separated string: 'table_name|query_string'. Example: 'sys_user|active=true^nameLIKEAlice'"

    def _run(self, input_str: str) -> str:
        try:
            table, query = input_str.split('|', 1)
        except ValueError:
            return "Error: Input must be in format 'table_name|query_string'"

        url = f"{INSTANCE_URL}/api/now/table/{table.strip()}"
        params = {
            'sysparm_query': query.strip(),
            'sysparm_limit': 5,
            'sysparm_display_value': 'true'
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
                    return "No records found."
                return json.dumps(results, indent=2)
            else:
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Connection Failed: {str(e)}"

class ServiceNowCreateTool(BaseTool):
    name: str = "ServiceNow Create Record"
    description: str = "Creates a new record in any ServiceNow table. Input should be a pipe-separated string: 'table_name|json_data'. Example: 'incident|{\"short_description\": \"Server outage\", \"urgency\": \"1\"}'"

    def _run(self, input_str: str) -> str:
        try:
            table, data_str = input_str.split('|', 1)
            data = json.loads(data_str.strip())
        except ValueError:
            return "Error: Input must be in format 'table_name|json_data'"
        except json.JSONDecodeError:
            return "Error: Invalid JSON data provided."

        url = f"{INSTANCE_URL}/api/now/table/{table.strip()}"
        
        try:
            response = requests.post(
                url, 
                auth=(USERNAME, PASSWORD), 
                headers={"Content-Type": "application/json"}, 
                json=data
            )
            if response.status_code == 201:
                result = response.json().get('result', {})
                return f"Success! Record created. SysID: {result.get('sys_id')} \nNumber: {result.get('number')}"
            else:
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Connection Failed: {str(e)}"

class ServiceNowUpdateTool(BaseTool):
    name: str = "ServiceNow Update Record"
    description: str = "Updates an existing record. Input should be a pipe-separated string: 'table_name|sys_id|json_data'. Example: 'incident|abc12345|{\"state\": \"2\"}'"

    def _run(self, input_str: str) -> str:
        try:
            parts = input_str.split('|', 2)
            if len(parts) != 3:
                raise ValueError
            table, sys_id, data_str = parts
            data = json.loads(data_str.strip())
        except ValueError:
            return "Error: Input must be in format 'table_name|sys_id|json_data'"
        except json.JSONDecodeError:
            return "Error: Invalid JSON data provided."

        url = f"{INSTANCE_URL}/api/now/table/{table.strip()}/{sys_id.strip()}"
        
        try:
            response = requests.put(
                url, 
                auth=(USERNAME, PASSWORD), 
                headers={"Content-Type": "application/json"}, 
                json=data
            )
            if response.status_code == 200:
                result = response.json().get('result', {})
                return f"Success! Record updated. SysID: {result.get('sys_id')}"
            else:
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Connection Failed: {str(e)}"
