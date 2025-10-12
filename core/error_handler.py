# core/error_handler.py
import json
import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from core.api_helper import explain_with_huggingface
import requests
from dotenv import load_dotenv
from pathlib import Path

ERROR_DB = "data/errors.json"
MODEL_PATH = "models/error_classifier.pkl"

# ✅ Load known errors safely
def load_errors():
    if not os.path.exists(ERROR_DB):
        return []
    try:
        with open(ERROR_DB, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("⚠️ Error: Could not decode errors.json")
        return []

# ✅ Load AI model if available
def load_model():
    if not os.path.exists(MODEL_PATH):
        return None, None
    try:
        with open(MODEL_PATH, "rb") as f:
            model_data = pickle.load(f)
        return model_data.get("model"), model_data.get("vectorizer")
    except Exception as e:
        print(f"⚠️ Model loading failed: {e}")
        return None, None

def explain_error(error_message):
    """Explain an error using local DB, AI model, or Hugging Face fallback."""
    errors = load_errors()
    model, vectorizer = load_model()

    # Step 1 → Look for known pattern in errors.json
    for err in errors:
        msg = err.get("error_message", "").lower()
        if msg and msg in error_message.lower():
            category = err.get("category", "Unknown")
            explanation = f"📘 This error matches a known example of **{category}**."
            fix_hint = f"💡 Try reviewing your code for issues related to **{category}**."
            example = f"Example: Check your index range, key existence, or attribute name depending on the type."
            return explanation, fix_hint, example

    # Step 2 → Use trained local model if available
    if model and vectorizer:
        try:
            X = vectorizer.transform([error_message])
            predicted_category = model.predict(X)[0]
            explanation = f"🤖 AI detected this might be a **{predicted_category}**."
            fix_hint = {
                "IndexError": "Ensure you’re not accessing out-of-range elements in lists or strings.",
                "KeyError": "Double-check that dictionary keys exist before accessing them.",
                "AttributeError": "Verify the variable type supports the attribute or method being called.",
                "LogicError": "Your code logic might not match your intended outcome. Try printing intermediate results."
            }.get(predicted_category, "Try rechecking your logic or reviewing variable usage.")
            example = f"Example fix for **{predicted_category}** could involve validating data or conditions before use."
            return explanation, fix_hint, example
        except Exception as e:
            return None, f"⚠️ AI prediction failed: {e}", None

    # Step 3 → Fallback to Hugging Face API
    result = call_huggingface_fallback(error_message)
    if isinstance(result, tuple):
        if len(result) == 3:
            return result
        else:
            return result[:3]
    else:
        return result, None, None


# Load Hugging Face API key
load_dotenv(dotenv_path=Path(".") / ".env")
HF_TOKEN = os.getenv("HF_API_TOKEN")

def call_huggingface_fallback(error_message):
    """Send unknown error to Hugging Face zero-shot model and get probable category."""
    if not HF_TOKEN:
        return "⚠️ API key missing", "Please configure HF_API_TOKEN in .env", None

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
    data = {
        "inputs": error_message,
        "parameters": {
            "candidate_labels": [
                "SyntaxError", "NameError", "IndexError",
                "KeyError", "AttributeError", "LogicError"
            ]
        }
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=8)
        if response.status_code == 200:
            result = response.json()
            best_label = result["labels"][0]
            confidence = result["scores"][0]
            explanation = f"The error likely belongs to **{best_label}** category (confidence: {confidence:.2f})."
            fix_hint = "You can review your code based on this category."
            return explanation, fix_hint, None
        else:
            return f"⚠️ API error {response.status_code}", "Could not classify error.", None
    except Exception as e:
        return f"⚠️ Exception during API call: {e}", "Network or API issue", None