# app/coding.py
import streamlit as st
import traceback
from io import StringIO
import sys
import time
from core.error_handler import explain_error, log_user_error
from core.progress import log_progress

def coding_practice(username):
    st.subheader("📝 Try Writing Python Code")

    # ✅ Safe defaults
    passed = 0
    total = 0
    duration = 0

    # ✅ Code editor
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
                st.write("Variables:", local_vars)

            passed, total = 1, 1
            log_user_error(username, "SuccessfulExecution")

        except Exception as e:
            error_message = str(e)
            st.error(f"❌ Error: {error_message}")

            # 🧠 AI Explanation
            explanation, fix_hint, example = explain_error(error_message)
            if explanation:
                st.info(f"{explanation}")
            if fix_hint:
                st.warning(f"💡 Hint: {fix_hint}")
            if example:
                st.code(example, language="python")

            # Detect category from explanation
            probable_category = None
            for cat in ["IndexError", "KeyError", "AttributeError", "LogicError", "NameError", "SyntaxError"]:
                if explanation and cat.lower() in explanation.lower():
                    probable_category = cat
                    break

            # Log user’s struggle category
            if probable_category:
                log_user_error(username, probable_category)
            else:
                log_user_error(username, "UnknownError")

            # Add concept review option
            if st.button("📚 Review Related Concept"):
                st.session_state.selected_page = "concepts"
                st.session_state.review_category = probable_category or "general"
                st.experimental_rerun()

            passed, total = 0, 1

        finally:
            sys.stdout = old_stdout
            duration = int(time.time() - start_time)
            log_progress(username, "free_practice", passed, total, code, duration)