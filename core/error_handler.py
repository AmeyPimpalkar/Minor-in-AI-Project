# core/error_handler.py
import json
import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer

ERROR_DB = "data/errors.json"
MODEL_PATH = "models/error_classifier.pkl"

# ✅ Load known errors
def load_errors():
    if not os.path.exists(ERROR_DB):
        return []
    with open(ERROR_DB, "r", encoding="utf-8") as f:
        return json.load(f)

# ✅ Load AI model
def load_model():
    if not os.path.exists(MODEL_PATH):
        return None, None
    with open(MODEL_PATH, "rb") as f:
        model_data = pickle.load(f)
    return model_data["model"], model_data["vectorizer"]

# ✅ Main explain function
def explain_error(error_message: str):
    errors = load_errors()
    model, vectorizer = load_model()

    # Step 1 → Try to find known error
    for err in errors:
        if err.get("error_message") and err["error_message"].lower() in error_message.lower():
            category = err.get("category", "Unknown")
            explanation = f"This error is categorized as **{category}**. It's likely caused by something similar to the known examples."
            fix_hint = f"Try reviewing {category} in your code."
            example = None
            return explanation, fix_hint, example

    # Step 2 → If unknown, use AI model to predict
    if model and vectorizer:
        try:
            X = vectorizer.transform([error_message])
            predicted_category = model.predict(X)[0]
            explanation = f"This seems to be related to **{predicted_category}**."
            fix_hint = {
                "IndexError": "Check your list or string indices. Make sure you aren’t accessing beyond range.",
                "KeyError": "Ensure the key exists in your dictionary before accessing it.",
                "AttributeError": "Check if the variable type supports the method or property you’re calling.",
                "LogicError": "Your logic may not match your intended outcome. Try printing intermediate values."
            }.get(predicted_category, "Try reviewing your logic for potential issues.")
            example = f"Example fix for {predicted_category} errors can often involve checking variable types or conditions."
            return explanation, fix_hint, example
        except Exception as e:
            return None, f"AI prediction failed: {e}", None

    # Step 3 → Total fallback
    return None, "Sorry, I couldn’t recognize this error. Please review your code manually or check docs.", None