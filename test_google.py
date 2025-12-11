import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")

def list_models():
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        models = response.json().get('models', [])
        print("Available Models:")
        for m in models:
            if 'generateContent' in m.get('supportedGenerationMethods', []):
                print(f" - {m['name']}")
    else:
        print(f"Error listing models: {response.status_code}")
        print(response.text)

def test_generate():
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
    data = {
        "contents": [{
            "parts": [{"text": "Hello, are you working?"}]
        }]
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        print("\nGeneration Test: SUCCESS")
        print(response.json())
    else:
        print(f"\nGeneration Test Failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    list_models()
    test_generate()
