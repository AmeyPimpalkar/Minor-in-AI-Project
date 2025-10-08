import json
import os
from core.ai_helper import predict_error_category

ERRORS_DB = "data/errors.json"

def load_errors():
    """Load error explanations safely from JSON."""
    if os.path.exists(ERRORS_DB):
        try:
            with open(ERRORS_DB, "r") as f:
                content = f.read().strip()
                if not content:  # if file is empty
                    return {}
                return json.loads(content)
        except json.JSONDecodeError:
            return {}
    return {}

def explain_error(error_message):
    # 1️⃣ Try exact match from errors.json
    # 2️⃣ If not found, use the AI model
    prediction = predict_error_category(error_message)
    if prediction["confidence"] > 0.65:
        category = prediction["category"]
        explanation = errors.get(category, {}).get("explanation")
        fix_hint = errors.get(category, {}).get("fix_hint")
        example = errors.get(category, {}).get("example")
        return explanation, fix_hint, example
    else:
        return "I'm not sure about this error.", "Try checking syntax or logic.", None