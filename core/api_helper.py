import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# Load API key from .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def explain_with_gemini(prompt):
    if not GEMINI_API_KEY:
        return "⚠️ Gemini API key missing or not loaded. Check your .env file."

    model_name = "gemini-2.5-flash"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"

    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        print(f"🔗 Sending request to Gemini model: {model_name}...")
        response = requests.post(url, headers=headers, params=params, json=data, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            # Safely extract the text from the response
            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text")
            if text:
                print("✅ Success! Received response from Gemini.")
                return text.strip()
            else:
                return "⚠️ Gemini returned an empty response."
        else:
            # Provide a detailed error from the server
            return f"⚠️ Gemini API Error: {response.status_code}\n{response.text}"

    except requests.exceptions.ReadTimeout:
        return "⚠️ Gemini API Error: The request timed out. The server is taking too long."
    except Exception as e:
        return f"⚠️ An unexpected error occurred: {e}"

