# app/coding.py
import streamlit as st
import traceback
from io import StringIO
import sys
import time
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

# Coding practice section
def coding_practice(username):
    st.subheader("Try Writing Python Code")

    passed = 0
    total = 0
    duration = 0
    probable_category = None
    code = st.text_area("Write your Python code here:", height=200)

    if st.button("▶️ Run Code"):
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

            # Run style & best-practice analysis
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

            if example:
                st.code(example, language="python")

            # Log user’s struggle
            log_user_error(username, probable_category or "UnknownError")

            # Dynamic concept linking
            if probable_category:
                if st.button("📚 Review Related Concept"):
                    st.session_state.selected_page = "concepts"
                    st.session_state.review_category = probable_category.lower().replace("error", "")
                    st.switch_page("app/concepts.py")
            else:
                if st.button("📚 Review General Concepts"):
                    st.session_state.selected_page = "concepts"
                    st.session_state.review_category = "general"
                    st.switch_page("app/concepts.py")

            passed, total = 0, 1

        finally:
            sys.stdout = old_stdout
            duration = int(time.time() - start_time)
            log_progress(username, "free_practice", passed, total, code, duration)

        # Reinforcement feedback
        reinforcement = get_reinforcement_message(username, probable_category)
        if reinforcement:
            st.info(reinforcement)
            if st.button("📘 Review Now", key=f"review_{probable_category}"):
                st.session_state.selected_page = "concepts"
                st.session_state.review_category = probable_category.lower()
                st.switch_page("app/concepts.py")