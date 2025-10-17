import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# Load .env from root
load_dotenv(dotenv_path=Path(".") / ".env")

HF_TOKEN = os.getenv("HF_API_TOKEN")
print("✅ Token loaded:", bool(HF_TOKEN))

if not HF_TOKEN:
    print("❌ Token not found. Check your .env file location or name.")
    exit()

# Test call
url = "https://api-inference.huggingface.co/models/google/flan-t5-base"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}
payload = {"inputs": "Explain Python NameError simply."}

print("🔗 Sending request...")
resp = requests.post(url, headers=headers, json=payload)

print("📦 Status code:", resp.status_code)
print("📄 Response:", resp.text)