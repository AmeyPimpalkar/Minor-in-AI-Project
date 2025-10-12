# core/api_helper.py
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

HF_API_TOKEN = os.getenv("HF_API_TOKEN")

def explain_with_huggingface(prompt: str):
    """
    Sends a prompt to Hugging Face API and returns the model's response.
    """
    if not HF_API_TOKEN:
        return "⚠️ Hugging Face API token not found. Please check your .env file."

    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    
    # You can change this model name to something better suited for explanation
    model = "gpt2"
    api_url = f"https://api-inference.huggingface.co/models/{model}"

    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 200}
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0 and "generated_text" in data[0]:
            return data[0]["generated_text"]
        else:
            return "⚠️ Unexpected response format from Hugging Face API."

    except requests.exceptions.RequestException as e:
        return f"❌ Error communicating with Hugging Face API: {str(e)}"