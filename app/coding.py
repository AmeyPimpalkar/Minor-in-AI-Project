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


# Basic dictionary to provide real explanations
ERROR_EXPLANATIONS = {
    "NameError": "This happens when you try to use a variable or function that hasn’t been defined yet. "
                 "For example, using `print(x)` before assigning a value to `x`.",
    "IndexError": "You’re trying to access an index that doesn’t exist in a list or string. "
                  "Example: accessing `my_list[5]` when it only has 3 elements.",
    "KeyError": "This occurs when you try to access a dictionary key that doesn’t exist. "
                "Example: `data['name']` when 'name' isn’t one of the keys.",
    "AttributeError": "You’re calling a method or property that doesn’t belong to that type of object. "
                      "Example: `5.append(2)` or `'hello'.push('!')`.",
    "LogicError": "The code runs fine but gives incorrect output — this usually means a flaw in logic, not syntax.",
    "SyntaxError": "Python can’t understand your code due to incorrect syntax. "
                   "Check for missing colons, parentheses, or indentation."
}


# --- Load revise_concepts.json ---
def load_revise_data():
    path = "data/revise_concepts.json"
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# --- Track repeated user mistakes ---
def increment_error_count(category):
    if "error_counts" not in st.session_state:
        st.session_state["error_counts"] = {}
    st.session_state["error_counts"][category] = st.session_state["error_counts"].get(category, 0) + 1


# --- Safe Gemini helper ---
def simplify_error_with_api(user_code, error_message):
    # Initialize list in session state if it doesn't exist
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
        # Append the new explanation to the list
        st.session_state['ai_explanations'].append(response)
    except Exception as e:
        st.session_state['ai_explanations'].append(f"⚠️ API Error: {e}")


def simplify_concept_with_api(concept_key):
    try:
        response = explain_with_gemini(f"Explain the Python concept '{concept_key}' in a simple way with a short example.")
        st.session_state["ai_concept_explanation"] = response
    except Exception as e:
        st.session_state["ai_concept_explanation"] = f"⚠️ API Error: {e}"


# --- Main Function ---
def coding_practice(username):
    st.subheader("🧑‍💻 Try Writing Python Code")

    # Initialize state for user code if it doesn't exist
    if 'user_code' not in st.session_state:
        st.session_state['user_code'] = ""

    revise_data = load_revise_data()
    st.session_state['user_code'] = st.text_area("Write your Python code here:", value=st.session_state['user_code'], height=200)
    
    passed = 0
    total = 0

    if st.button("▶️ Run Code"):
        # Clear previous run results from session state
        st.session_state.pop("error_message", None)
        st.session_state.pop("ai_explanations", None)
        st.session_state.pop("execution_output", None)
        st.session_state.pop("probable_category", None)
        st.session_state.pop("fix_hint", None)
        st.session_state.pop("example", None)
        
        start_time = time.time()
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()

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
            st.session_state['fix_hint'] = fix_hint
            st.session_state['example'] = example
            
            probable_category = None
            for cat in ERROR_EXPLANATIONS.keys():
                if explanation and cat.lower() in explanation.lower():
                    probable_category = cat
                    break
            st.session_state['probable_category'] = probable_category
            
            if probable_category:
                increment_error_count(probable_category.lower())

            log_user_error(username, probable_category or "UnknownError")

        finally:
            sys.stdout = old_stdout
            duration = int(time.time() - start_time)
            log_progress(username, "free_practice", passed, total, st.session_state['user_code'], duration)

    # --- DISPLAY LOGIC (runs on every interaction) ---

    # Display success output if it exists in state
    if st.session_state.get("execution_output"):
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

    # Display error information if an error exists in state
    if st.session_state.get("error_message"):
        st.error(f"❌ Error: {st.session_state['error_message']}")
        
        probable_category = st.session_state.get("probable_category")
        if probable_category:
            st.info(f"📘 **What is {probable_category}?**\n\n{ERROR_EXPLANATIONS[probable_category]}")
            st.warning(f"💡 Hint: {st.session_state.get('fix_hint') or 'Try reviewing this concept in detail.'}")
        else:
            st.info("🤔 Could not classify this error clearly.")
            st.warning(f"💡 Hint: {st.session_state.get('fix_hint') or 'Try reviewing your logic or syntax.'}")

        # ✅ SIMPLIFY BUTTON (now it works!)
        if st.button("🤖 Simplify This Error"):
            with st.spinner("Simplifying error explanation using Gemini..."):
                simplify_error_with_api(st.session_state['user_code'], st.session_state['error_message'])
        
        # Display all AI explanations stored in the list
        if st.session_state.get('ai_explanations'):
            st.write("---")
            st.subheader("🤖 AI Assistant's Explanations:")
            # Loop in reverse to show the newest explanation first
            for explanation in reversed(st.session_state['ai_explanations']):
                st.info(explanation)
                st.markdown("---")


        if st.session_state.get('example'):
            st.code(st.session_state['example'], language="python")

        # Logic for revising concepts
        if probable_category and st.session_state.get("error_counts", {}).get(probable_category.lower(), 0) > 1:
            with st.expander("📚 Revise Related Concept", expanded=True):
                concept_key = probable_category.lower().replace("error", "")
                if concept_key in revise_data:
                    concept = revise_data[concept_key]
                    st.markdown(f"### 🔹 {concept.get('title', concept_key.capitalize())}")
                    st.write(concept.get("summary", "No summary available."))

                    if concept.get("example"):
                        st.code(concept["example"], language="python")
                    if concept.get("tip"):
                        st.success(f"💡 {concept['tip']}")
                    if concept.get("analogy"):
                        st.info(f"🌱 Analogy: {concept['analogy']}")

                    if st.button("🤖 Simplify Concept Explanation"):
                        with st.spinner("Fetching simpler explanation from Gemini..."):
                            simplify_concept_with_api(concept_key)

                    if "ai_concept_explanation" in st.session_state:
                        st.info(st.session_state["ai_concept_explanation"])
                else:
                    st.warning("Concept details not found in revise_concepts.json")
    
    # Reinforcement message logic (runs regardless of error)
    reinforcement = get_reinforcement_message(username, st.session_state.get("probable_category"))
    if reinforcement and not st.session_state.get("execution_output"): # Only show on error runs
        st.info(reinforcement)
