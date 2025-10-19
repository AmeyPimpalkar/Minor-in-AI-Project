import streamlit as st
import traceback
from io import StringIO
import sys
import time
import json
import os

from core.error_handler import explain_error, log_user_error, get_reinforcement_message
from core.progress import log_progress
from core.code_analyzer import analyze_code_style
from core.api_helper import explain_with_gemini
from app.concepts import ERROR_TO_CONCEPT 

ERROR_EXPLANATIONS = {
    "NameError": "This happens when you try to use a variable or function that hasn’t been defined yet...",
    "IndexError": "You’re trying to access an index that doesn’t exist in a list or string...",
    "KeyError": "This occurs when you try to access a dictionary key that doesn’t exist...",
    "AttributeError": "You’re calling a method or property that doesn’t belong to that type of object...",
    "LogicError": "The code runs fine but gives incorrect output...",
    "SyntaxError": "Python can’t understand your code due to incorrect syntax..."
}

# Track repeated user mistakes.
def increment_error_count(category):
    if "error_counts" not in st.session_state:
        st.session_state["error_counts"] = {}
    category_lower = category.lower() if category else "unknown"
    st.session_state["error_counts"][category_lower] = st.session_state["error_counts"].get(category_lower, 0) + 1


# Fetch API.
def simplify_error_with_api(user_code, error_message):
    if 'ai_explanations' not in st.session_state:
        st.session_state['ai_explanations'] = []
    previous_explanations = "\n---\n".join(st.session_state['ai_explanations'])
    prompt = ""

    if previous_explanations:
        prompt = (
            f"A beginner is still confused about an error in their Python code. "
            f"Here is their code:\n\n```python\n{user_code}\n```\n\n"
            f"The error is:\n`{error_message}`\n\n"
            f"You already provided these explanations:\n{previous_explanations}\n\n"
            f"Please provide another explanation, but use a completely different analogy or a simpler perspective. Be very encouraging."
        )
    else:
        prompt = (
            f"Explain this Python error in very simple, beginner-friendly terms. "
            f"The error is:\n`{error_message}`\n\n"
            f"The user wrote this code:\n\n```python\n{user_code}\n```\n\n"
            f"Tell them what's wrong and how to fix it in their specific code."
        )

    try:
        response = explain_with_gemini(prompt)
        st.session_state['ai_explanations'].append(response)
    except Exception as e:
        st.session_state['ai_explanations'].append(f"⚠️ API Error: {e}")


def simplify_concept_with_api(concept_key):
    try:
        response = explain_with_gemini(f"Explain the Python concept '{concept_key}' in a simple way with a short example.")
        st.session_state["ai_concept_explanation"] = response
    except Exception as e:
        st.session_state["ai_concept_explanation"] = f"⚠️ API Error: {e}"


# Main Function Section. (IMP)
def coding_practice(username):
    st.subheader("🧑‍💻 Try Writing Python Code")

    if 'user_code' not in st.session_state:
        st.session_state['user_code'] = ""

    user_code_input = st.text_area("Write your Python code here:", value=st.session_state['user_code'], height=200, key="coding_practice_input")
    st.session_state['user_code'] = user_code_input

    passed = 0
    total = 0
    duration = 0

    if st.button("▶️ Run Code"):
        # Clear previous run results
        st.session_state.pop("error_message", None)
        st.session_state.pop("ai_explanations", None)
        st.session_state.pop("execution_output", None)
        st.session_state.pop("probable_category", None)
        st.session_state.pop("fix_hint", None)
        st.session_state.pop("example", None)

        start_time = time.time()
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        predicted_category_from_ai = None

        try:
            local_vars = {}
            exec(st.session_state['user_code'], {}, local_vars)
            st.session_state['execution_output'] = mystdout.getvalue()
            passed, total = 1, 1
            log_user_error(username, "SuccessfulExecution")

        except Exception as e:
            error_message = str(e)
            st.session_state['error_message'] = error_message
            explanation, fix_hint, example, predicted_category_from_ai = explain_error(error_message, username)
            # Store results in session state for display logic below
            st.session_state['explanation'] = explanation
            st.session_state['fix_hint'] = fix_hint
            st.session_state['example'] = example
            st.session_state['probable_category'] = predicted_category_from_ai

            # Increment count and log 
            if predicted_category_from_ai:
                increment_error_count(predicted_category_from_ai)
                # Ensure log_user_error is called 
            else:
                log_user_error(username, "UnknownError")

        finally:
            sys.stdout = old_stdout
            duration = int(time.time() - start_time)
            log_progress(username, "free_practice", passed, total, st.session_state['user_code'], duration)

# Display Logic 

    # Display success output
    if "execution_output" in st.session_state:
        output = st.session_state.get("execution_output", "")
        if output.strip():
            st.success("✅ Code ran successfully!")
            st.text("📤 Output:")
            st.code(output, language="text")
        else:
            st.success("✅ Code ran successfully but no output was printed.")

        ai_feedback = analyze_code_style(st.session_state['user_code'])
        if ai_feedback:
            st.markdown("### 💡 Code Improvement Suggestions")
            st.write(ai_feedback)

    # Display error information
    if "error_message" in st.session_state:
        st.error(f"❌ Error: {st.session_state['error_message']}")

        probable_category = st.session_state.get('probable_category')
        explanation = st.session_state.get('explanation', "Could not get explanation.")
        fix_hint = st.session_state.get('fix_hint', "Try reviewing your logic or syntax.")
        example = st.session_state.get('example')

        if probable_category:
             st.info(f"AI Model thinks this might be a **{probable_category}**.")

        st.info(f"Explanation: {explanation}")
        st.warning(f"💡 Hint: {fix_hint}")
        if example:
            st.code(example, language="python")

        # Simplify Button Logic.
        if st.button("🤖 Simplify This Error"):
            with st.spinner("Simplifying error explanation using Gemini..."):
                simplify_error_with_api(st.session_state['user_code'], st.session_state['error_message'])

        if st.session_state.get('ai_explanations'):
            st.write("---")
            st.subheader("🤖 AI Assistant's Additional Explanations:")
            for exp in reversed(st.session_state['ai_explanations']):
                st.info(exp)
                st.markdown("---")

    # Reinforcement message logic. 
    reinforcement_data = get_reinforcement_message(username, st.session_state.get("probable_category"))
    # Only show if reinforcement triggered AND there was an error
    if reinforcement_data and "error_message" in st.session_state:
        reinforcement_message = ""
        if isinstance(reinforcement_data, dict):
            reinforcement_message = reinforcement_data.get("message", "")
        elif isinstance(reinforcement_data, str):
             reinforcement_message = reinforcement_data

        if reinforcement_message: # Check if message is not empty
            st.info(reinforcement_message) # Display reinforcement message

            # Revise Concepts Button
            probable_category_for_button = st.session_state.get('probable_category')
            if probable_category_for_button:
                concept_key_to_revise = ERROR_TO_CONCEPT.get(probable_category_for_button)

                if concept_key_to_revise:
                    button_label = f"📚 Revise Concept: {concept_key_to_revise.capitalize()}"
                    button_key = f"revise_{probable_category_for_button}_{int(time.time())}" # Unique key

                    if st.button(button_label, key=button_key):
                        revise_file_path = "data/revise_concepts.json"
                        try:
                            os.makedirs(os.path.dirname(revise_file_path), exist_ok=True)
                            review_request = {
                                "last_review": {
                                    "category": concept_key_to_revise,
                                    "timestamp": time.time()
                                }
                            }
                            existing_data = {}
                            if os.path.exists(revise_file_path):
                                 with open(revise_file_path, "r", encoding="utf-8") as f_read:
                                     try: existing_data = json.load(f_read)
                                     except json.JSONDecodeError: pass
                            existing_data.update(review_request)
                            with open(revise_file_path, "w", encoding="utf-8") as f_write:
                                json.dump(existing_data, f_write, indent=2)
                            st.success(f"Okay, navigate to the 'Concepts' tab to revise **{concept_key_to_revise}**.")
                        except Exception as write_error:
                            st.error(f"Could not save revision request: {write_error}")