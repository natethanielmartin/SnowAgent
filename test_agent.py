import os
import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

# Configuration
INSTANCE_URL = "https://dev309858.service-now.com" # I pulled this from your screenshot
USERNAME = os.getenv("SN_USERNAME")
PASSWORD = os.getenv("SN_PASSWORD")

def check_connection():
    # We will try to fetch 1 Knowledge Article to prove it works
    url = f"{INSTANCE_URL}/api/now/table/kb_knowledge"
    
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    params = {
        "sysparm_limit": 1,
        "sysparm_fields": "short_description,number"
    }

    print(f"🔌 Connecting to {INSTANCE_URL}...")
    
    response = requests.get(
        url, 
        auth=HTTPBasicAuth(USERNAME, PASSWORD), 
        headers=headers, 
        params=params
    )

    if response.status_code == 200:
        data = response.json()
        print("✅ SUCCESS! Connection established.")
        print("Agent found this article:", data['result'][0])
    else:
        print(f"❌ ERROR: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    check_connection()