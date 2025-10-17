# core/api_helper.py
import os
import requests
import time
from dotenv import load_dotenv
from pathlib import Path

# Load .env
load_dotenv(dotenv_path=Path(".") / ".env")
HF_TOKEN = os.getenv("HF_API_TOKEN")

HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}

# ✅ Stable text generation models currently supported on HF inference API
EXPLAIN_MODELS = [
    "meta-llama/Llama-3.2-1B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.2",
    "HuggingFaceH4/zephyr-7b-beta"
]

def _post_with_retries(url, payload, headers=None, timeout=15, retries=2, backoff=1.5):
    headers = headers or HEADERS
    for attempt in range(retries + 1):
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=timeout)
            if r.status_code == 200:
                return r
            time.sleep(backoff ** attempt)
        except Exception as e:
            if attempt == retries:
                raise
            time.sleep(backoff ** attempt)
    return None

def explain_with_huggingface(prompt, max_new_tokens=150):
    """Generate a simple explanation for the given text."""
    if not HF_TOKEN:
        return "⚠️ HF token missing. Add HF_API_TOKEN in your .env file."

    for model in EXPLAIN_MODELS:
        url = f"https://api-inference.huggingface.co/models/{model}"
        payload = {
            "inputs": prompt,
            "parameters": {"max_new_tokens": max_new_tokens},
            "options": {"wait_for_model": True}
        }

        try:
            print(f"🔗 Testing model: {model}")  # Optional for debugging
            r = _post_with_retries(url, payload)
            if not r:
                continue

            if r.status_code == 200:
                j = r.json()
                if isinstance(j, list) and len(j) and "generated_text" in j[0]:
                    return j[0]["generated_text"].strip()
                elif isinstance(j, dict) and "generated_text" in j:
                    return j["generated_text"].strip()
                else:
                    return str(j)
            elif r.status_code == 503:
                return "⚠️ Model is loading on Hugging Face. Please retry in a few seconds."
            else:
                continue
        except Exception as e:
            continue

    return "⚠️ Could not get a response from external models. Try again later."