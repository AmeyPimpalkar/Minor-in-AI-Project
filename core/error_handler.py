# core/error_handler.py
import json
import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from core.api_helper import explain_with_huggingface

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

# ✅ Explain errors using both static DB + AI model
def explain_error(error_message: str):
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

    # Step 2 → If unknown, ask the AI model to classify
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

    # Step 3 → Total fallback
    return None, "❌ Couldn’t recognize this error. Try revisiting your logic or checking documentation.", None


def explain_error(error_message):
    # Your existing explanation logic here...
    # If local model can't recognize:
    hf_response = explain_with_huggingface(f"Explain this Python error in simple terms: {error_message}")
    return hf_response