import json
import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
# Import the Gemini helper function (ensure this path is correct)
from core.api_helper import explain_with_gemini
import streamlit as st # Keep streamlit for st.spinner potentially inside explain_with_gemini

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
def get_reinforcement_message(username, category):
    """If user repeats same error multiple times, suggest concept revision."""
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
            # Ensure the returned dict matches expected structure if needed elsewhere
            return message # Returning only message string might be simpler if category/count aren't used by caller
            # Or return dict if needed:
            # return {
            #     "message": message,
            #     "category": category, # Pass category back if needed
            #     "count": count,       # Pass count back if needed
            #     "action": "review_concept"
            # }
    except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
        print(f"⚠️ Error reading or processing {USER_LOG}: {e}")
        pass

    return None


# Load known errors safely (No changes needed here)
def load_errors():
    if not os.path.exists(ERROR_DB):
        return []
    try:
        with open(ERROR_DB, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("⚠️ Error: Could not decode errors.json")
        return []


# Load AI model if available (Uses the corrected version from previous step)
def load_model():
    if not os.path.exists(MODEL_PATH):
        print(f"⚠️ Model file not found at: {MODEL_PATH}")
        return None # Return None if file doesn't exist

    try:
        with open(MODEL_PATH, "rb") as f:
            # Load the entire pipeline object directly
            pipeline_model = pickle.load(f)
        # Check if it's a scikit-learn pipeline (optional but good practice)
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
def explain_error(error_message, username=None):
    """Explain an error using local explanation DB, ML model, or Gemini fallback."""
    pipeline_model = load_model() # Load the single pipeline object or None

    # Step 0 → Try to match from explanation DB first
    if os.path.exists(EXPLANATION_DB):
        try:
            with open(EXPLANATION_DB, "r", encoding="utf-8") as f:
                explanations = json.load(f)

            # Allow partial match (e.g., “name” inside “NameError”)
            for category, info in explanations.items():
                # Make matching case-insensitive and handle 'error' suffix
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
                    # Return 4 values: explanation, hint, example, category
                    return (
                        formatted_explanation + (f"\n\n{reinforcement}" if reinforcement else ""),
                        "Here’s a detailed explanation of your error.",
                        example,
                        category # Return the matched category
                    )
        except Exception as e:
            print(f"⚠️ Could not load or process explanation DB: {e}")

    # Step 1 → Try AI model prediction
    if pipeline_model: # Check if the model loaded
        try:
            # Use the loaded pipeline directly for prediction
            predicted_category = pipeline_model.predict([error_message])[0]

            log_user_error(username, predicted_category)
            reinforcement = get_reinforcement_message(username, predicted_category)

            explanation = f"🤖 AI predicts this might be a **{predicted_category}**."
            fix_hint = "💡 Try reviewing this concept in the Concepts section, or check the explanation database."

            # Return 4 values: explanation, hint, example (None), category
            return (
                explanation + (f"\n\n{reinforcement}" if reinforcement else ""),
                fix_hint,
                None, # No specific code example from the model
                predicted_category # Return the predicted category
            )
        except Exception as e:
            print(f"⚠️ AI prediction failed: {e}")
            # Fall through to Gemini if prediction fails

    # Step 2 -> Fallback to Gemini API if DB match and AI prediction failed or skipped
    print("Falling back to Gemini API...")
    try:
        # Construct a simple prompt for Gemini
        gemini_prompt = (
            f"Explain this Python error in simple terms for a beginner:\n\n"
            f"Error message: `{error_message}`\n\n"
            f"Focus on what likely caused it and how to fix it."
        )
        # Use st.spinner for user feedback during API call
        with st.spinner("🤖 Asking Gemini for a simpler explanation..."):
             gemini_explanation = explain_with_gemini(gemini_prompt)

        # Basic check if Gemini returned an error message itself
        if gemini_explanation.startswith("⚠️"):
             hint = "Could not get explanation from Gemini."
             category = None # Cannot determine category from Gemini error
        else:
             hint = "Explanation provided by Gemini AI."
             category = None # Cannot reliably determine category from Gemini text

        # Return 4 values: explanation, hint, example (None), category (None)
        return gemini_explanation, hint, None, category

    except Exception as e:
        print(f"⚠️ Gemini fallback failed: {e}")
        # Final fallback if Gemini also fails
        return "⚠️ Could not get an explanation.", f"Error during Gemini fallback: {str(e)}", None, None

# --- REMOVED HUGGING FACE CODE ---
# (No need for HF_TOKEN, MODEL_URLS, call_huggingface_fallback function anymore)
# --- END REMOVED HUGGING FACE CODE ---