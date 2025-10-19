import json
import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from core.api_helper import explain_with_gemini
import streamlit as st 

# File paths
ERROR_DB = "data/errors.json"
MODEL_PATH = "models/error_classifier.pkl"
USER_LOG = "data/user_learning_log.json"
EXPLANATION_DB = "data/error_explanations.json"


# Log user mistakes and repetitions
def log_user_error(username, category):
    #Logs user mistakes by category for personalised feedback.
    if not username or not category:
        return

    if not os.path.exists(USER_LOG):
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(USER_LOG), exist_ok=True)
        with open(USER_LOG, "w", encoding="utf-8") as f:
            json.dump({}, f)

    try:
        with open(USER_LOG, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
    except FileNotFoundError:
         data = {} # Handle case where file might disappear between exists check and open

    if username not in data:
        data[username] = {}
    data[username][category] = data[username].get(category, 0) + 1

    try:
        with open(USER_LOG, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"⚠️ Failed to write to {USER_LOG}: {e}")


# Reinforcement logic
# If user repeats same error multiple times, suggest concept revision.
def get_reinforcement_message(username, category):
    if not username or not category or not os.path.exists(USER_LOG):
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
            return message 
            
    except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
        print(f"⚠️ Error reading or processing {USER_LOG}: {e}")
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
        print(f"⚠️ Model file not found at: {MODEL_PATH}")
        return None # Return None if file doesn't exist

    try:
        with open(MODEL_PATH, "rb") as f:
            # Load the entire pipeline object directly
            pipeline_model = pickle.load(f)
        # Check if it's a scikit-learn pipeline 
        if hasattr(pipeline_model, 'predict') and hasattr(pipeline_model, 'transform'):
             print("✅ Model pipeline loaded successfully.")
             return pipeline_model # Return the loaded pipeline
        else:
             print(f"⚠️ Loaded object from {MODEL_PATH} is not a valid scikit-learn pipeline.")
             return None
    except Exception as e:
        print(f"⚠️ Model loading failed from {MODEL_PATH}: {e}")
        return None # Return None on error


# Explain error with model or fallback
# Explain an error using local explanation DB, ML model, or Gemini fallback.
def explain_error(error_message, username=None):
    pipeline_model = load_model() 

    if os.path.exists(EXPLANATION_DB):
        try:
            with open(EXPLANATION_DB, "r", encoding="utf-8") as f:
                explanations = json.load(f)

            for category, info in explanations.items():
                error_lower = error_message.lower()
                cat_lower = category.lower()
                cat_no_error_lower = cat_lower.replace("error", "")

                if cat_lower in error_lower or (cat_no_error_lower and cat_no_error_lower in error_lower):
                    log_user_error(username, category)
                    reinforcement = get_reinforcement_message(username, category)

                    meaning = info.get("meaning", "No specific meaning available.")
                    cause = info.get("cause", "No specific cause listed.")
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
                        category # Return the matched category
                    )
        except Exception as e:
            print(f"⚠️ Could not load or process explanation DB: {e}")


    if pipeline_model: # Check if the model loaded
        try:
            predicted_category = pipeline_model.predict([error_message])[0]

            log_user_error(username, predicted_category)
            reinforcement = get_reinforcement_message(username, predicted_category)

            explanation = f"AI predicts this might be a **{predicted_category}**."
            fix_hint = "💡 Try reviewing this concept in the Concepts section, or check the explanation database."

            return (
                explanation + (f"\n\n{reinforcement}" if reinforcement else ""),
                fix_hint,
                None, 
                predicted_category 
            )
        except Exception as e:
            print(f"⚠️ AI prediction failed: {e}")


    print("Falling back to Gemini API...")
    try:
        gemini_prompt = (
            f"Explain this Python error in simple terms for a beginner:\n\n"
            f"Error message: `{error_message}`\n\n"
            f"Focus on what likely caused it and how to fix it."
        )
        with st.spinner("Asking Gemini for a simpler explanation..."):
             gemini_explanation = explain_with_gemini(gemini_prompt)

        if gemini_explanation.startswith("⚠️"):
             hint = "Could not get explanation from Gemini."
             category = None 
        else:
             hint = "Explanation provided by Gemini AI."
             category = None 

        return gemini_explanation, hint, None, category

    except Exception as e:
        print(f"⚠️ Gemini fallback failed: {e}")
        return "⚠️ Could not get an explanation.", f"Error during Gemini fallback: {str(e)}", None, None

