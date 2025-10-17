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
from core.api_helper import explain_with_huggingface


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


# Helper: call API safely and store result in session_state
def simplify_error_with_api(error_message):
    try:
        st.session_state["ai_error_explanation"] = explain_with_huggingface(
            f"Explain this Python error in very simple terms: {error_message}"
        )
    except Exception as e:
        st.session_state["ai_error_explanation"] = f"⚠️ API Error: {e}"

def simplify_concept_with_api(concept_key):
    try:
        st.session_state["ai_concept_explanation"] = explain_with_huggingface(
            f"Explain this Python concept '{concept_key}' in a very simple beginner way with short examples."
        )
    except Exception as e:
        st.session_state["ai_concept_explanation"] = f"⚠️ API Error: {e}"

# Load revise data
def load_revise_data():
    path = "data/revise_concepts.json"
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# Track how many times user failed per concept
def increment_error_count(category):
    if "error_counts" not in st.session_state:
        st.session_state["error_counts"] = {}
    st.session_state["error_counts"][category] = st.session_state["error_counts"].get(category, 0) + 1


def coding_practice(username):
    st.subheader("🧑‍💻 Try Writing Python Code")
    st.write("✅ Streamlit running. API test below:")
    if st.button("Test HuggingFace API"):
        try:
            response = explain_with_huggingface("Explain Python NameError simply.")
            st.success(response)
        except Exception as e:
            st.error(f"API Error: {e}")
    revise_data = load_revise_data()

    passed = 0
    total = 0
    duration = 0
    probable_category = None
    code = st.text_area("Write your Python code here:", height=200)

    if st.button("▶️ Run Code"):
        st.session_state.pop("ai_error_explanation", None)
        st.session_state.pop("ai_concept_explanation", None)
        start_time = time.time()
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()

        try:
            local_vars = {}
            exec(code, {}, local_vars)
            output = mystdout.getvalue()

            if output.strip():
                st.success("✅ Code ran successfully!")
                st.text("📤 Output:")
                st.code(output, language="text")
            else:
                st.success("✅ Code ran successfully but no output was printed.")

                # Detect function/class definitions without calls
                if any(line.strip().startswith(("def ", "class ")) for line in code.splitlines()):
                    st.info("💡 You defined a function or class but didn’t call it. Try calling it below to test your logic.")
                else:
                    st.write("Variables:", local_vars)

            # Style analysis
            ai_feedback = analyze_code_style(code)
            if ai_feedback:
                st.markdown("### 💡 Code Improvement Suggestions")
                st.write(ai_feedback)

            passed, total = 1, 1
            log_user_error(username, "SuccessfulExecution")

        except Exception as e:
            error_message = str(e)
            st.error(f"❌ Error: {error_message}")

            explanation, fix_hint, example = explain_error(error_message)
            probable_category = None

            # Detect probable error category
            for cat in ERROR_EXPLANATIONS.keys():
                if explanation and cat.lower() in explanation.lower():
                    probable_category = cat
                    break

            # Add real-world explanation
            if probable_category:
                st.info(f"📘 **What is {probable_category}?**\n\n{ERROR_EXPLANATIONS[probable_category]}")
                st.warning(f"💡 Hint: {fix_hint or 'Try reviewing this concept in detail.'}")
            else:
                st.info(explanation or "🤔 Could not classify this error clearly.")
                st.warning(f"💡 Hint: {fix_hint or 'Try reviewing your logic or syntax.'}")

            # First simplify button (for error)
            if st.button("🤖 Simplify This Error", key="simplify_error_btn"):
                with st.spinner("Simplifying the error..."):
                    simplify_error_with_api(error_message)

            # After the button, show the stored result if it exists
            if "ai_error_explanation" in st.session_state:
                st.info(st.session_state["ai_error_explanation"])

            if example:
                st.code(example, language="python")

            # Track repeated errors
            if probable_category:
                increment_error_count(probable_category.lower())

            # Log user’s struggle
            log_user_error(username, probable_category or "UnknownError")

            # Show related concept **only if user failed >1 time in same category**
            if probable_category and st.session_state["error_counts"].get(probable_category.lower(), 0) > 1:
                with st.expander("📚 Review Related Concept", expanded=True):
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

                        # Second simplify button (for concept)
                        if st.button("🤖 Fetch Simpler Explanation", key=f"simplify_concept_{probable_category}"):
                            with st.spinner("Rephrasing concept in simpler language..."):
                                simplify_concept_with_api(concept_key)

                        # Show stored result if it exists
                        if "ai_concept_explanation" in st.session_state:
                            st.info(st.session_state["ai_concept_explanation"])
                    else:
                        st.warning("Concept details not found in revise_concepts.json")

            passed, total = 0, 1

        finally:
            sys.stdout = old_stdout
            duration = int(time.time() - start_time)
            log_progress(username, "free_practice", passed, total, code, duration)

        # Reinforcement feedback
        reinforcement = get_reinforcement_message(username, probable_category)
        if reinforcement:
            st.info(reinforcement)