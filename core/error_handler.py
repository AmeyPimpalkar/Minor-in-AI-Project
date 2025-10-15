
import json
import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from core.api_helper import explain_with_huggingface
import requests
from dotenv import load_dotenv
from pathlib import Path
import requests
import concurrent.futures
import streamlit as st

# File paths
ERROR_DB = "data/errors.json"
MODEL_PATH = "models/error_classifier.pkl"
USER_LOG = "data/user_learning_log.json"
EXPLANATION_DB = "data/error_explanations.json"


# Log user mistakes and repetitions
def log_user_error(username, category):
    """Logs user mistakes by category for personalized feedback."""
    if not username or not category:
        return

    if not os.path.exists(USER_LOG):
        with open(USER_LOG, "w", encoding="utf-8") as f:
            json.dump({}, f)

    with open(USER_LOG, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}

    if username not in data:
        data[username] = {}
    data[username][category] = data[username].get(category, 0) + 1

    with open(USER_LOG, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# Reinforcement logic
def get_reinforcement_message(username, category):
    """If user repeats same error multiple times, suggest concept revision."""
    if not username or not os.path.exists(USER_LOG):
        return None

    try:
        with open(USER_LOG, "r", encoding="utf-8") as f:
            data = json.load(f)
        count = data.get(username, {}).get(category, 0)

        if count >= 3:
            message = (
                f" You've encountered **{category}** errors {count} times. "
                "Consider reviewing this concept in the Learn section."
            )
            return {
                "message": message,
                "category": category,
                "count": count,
                "action": "review_concept"
            }
    except Exception:
        pass

    return None


# Load known errors safely
def load_errors():
    if not os.path.exists(ERROR_DB):
        return []
    try:
        with open(ERROR_DB, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("⚠️ Error: Could not decode errors.json")
        return []


# Load AI model if available
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


# Explain error with model or fallback
def explain_error(error_message, username=None):
    """Explain an error using local explanation DB, ML model, or Hugging Face fallback."""
    model, vectorizer = load_model()

    # Step 0 → Try to match from explanation DB first
    if os.path.exists(EXPLANATION_DB):
        try:
            with open(EXPLANATION_DB, "r", encoding="utf-8") as f:
                explanations = json.load(f)

            # Allow partial match (e.g., “name” inside “NameError”)
            for category, info in explanations.items():
                if category.lower() in error_message.lower() or category.lower().replace("error", "") in error_message.lower():
                    log_user_error(username, category)
                    reinforcement = get_reinforcement_message(username, category)

                    meaning = info.get("meaning", "")
                    cause = info.get("cause", "")
                    fixes = info.get("fix", [])
                    example = info.get("example", "")

                    formatted_explanation = (
                        f"### 🧠 What it means:\n{meaning}\n\n"
                        f"### ⚙️ Why it happens:\n{cause}\n\n"
                        f"### 🛠️ How to fix it:\n"
                        + "".join([f"- {fix}\n" for fix in fixes])
                    )

                    return (
                        formatted_explanation + (f"\n\n{reinforcement}" if reinforcement else ""),
                        "Here’s a detailed explanation of your error.",
                        example,
                    )
        except Exception as e:
            print(f"⚠️ Could not load explanation DB: {e}")

    # Try AI model prediction
    if model and vectorizer:
        try:
            X = vectorizer.transform([error_message])
            predicted_category = model.predict(X)[0]
            log_user_error(username, predicted_category)
            reinforcement = get_reinforcement_message(username, predicted_category)

            explanation = f"🤖 AI predicts this might be a **{predicted_category}**."
            fix_hint = "💡 Try reviewing this concept in the Concepts section."
            return (
                explanation + (f"\n\n{reinforcement}" if reinforcement else ""),
                fix_hint,
                None,
            )
        except Exception as e:
            print(f"⚠️ AI prediction failed: {e}")

    # Fallback to Hugging Face parallel API
    result = call_huggingface_fallback(error_message)
    if isinstance(result, tuple):
        explanation, fix_hint, example = result

        # Try to extract probable label and log it
        for label in ["SyntaxError", "NameError", "IndexError", "KeyError", "AttributeError", "LogicError"]:
            if label.lower() in explanation.lower():
                log_user_error(username, label)
                reinforcement = get_reinforcement_message(username, label)
                return (
                    explanation + (f"\n\n{reinforcement}" if reinforcement else ""),
                    fix_hint,
                    example,
                )
        return result
    else:
        return result, None, None
    

# Load Hugging Face API key
load_dotenv(dotenv_path=Path(".") / ".env")
HF_TOKEN = os.getenv("HF_API_TOKEN")


# Hugging Face fallback function
MODEL_URLS = [
    "https://api-inference.huggingface.co/models/facebook/bart-large-mnli",
    "https://api-inference.huggingface.co/models/distilbert-base-uncased-mnli",
    "https://api-inference.huggingface.co/models/MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
]

def call_huggingface_fallback(error_message):
    """Send unknown error to multiple Hugging Face zero-shot models in parallel and get probable category."""
    if not HF_TOKEN:
        return "⚠️ API key missing", "Please configure HF_API_TOKEN in .env", None

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "inputs": error_message,
        "parameters": {
            "candidate_labels": [
                "SyntaxError", "NameError", "IndexError",
                "KeyError", "AttributeError", "LogicError"
            ]
        }
    }

    def request_model(url):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=8)
            if response.status_code == 200:
                return url, response.json()
            return url, None
        except Exception:
            return url, None

    # Show loading spinner in Streamlit UI
    with st.spinner("🤖 Analyzing your error... please wait a few seconds..."):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(request_model, url): url for url in MODEL_URLS}
            for future in concurrent.futures.as_completed(futures):
                url, result = future.result()
                if result:
                    best_label = result["labels"][0]
                    confidence = result["scores"][0]
                    explanation = f"The error likely belongs to **{best_label}** category (confidence: {confidence:.2f})."
                    fix_hint = f"This usually occurs when something in your code triggers a **{best_label}**. Review related syntax or logic."
                    return explanation, fix_hint, None

    # If none succeeded
    return "⚠️ All models failed to respond.", "Please check your internet connection or try again later.", None