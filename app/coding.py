# app/coding.py
import streamlit as st
import traceback
from io import StringIO
import sys
import time
# from st_ace import st_ace  # Re-importing after reinstallation
from core.error_handler import explain_error
from core.progress import log_progress

def coding_practice(username):
    st.subheader("📝 Try Writing Python Code")

    # ✅ Code editor instead of text_area
    code = st.text_area("Write your Python code here:", height=200)

    if st.button("Run Code"):
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
                passed, total = 1, 1
            else:
                st.success("✅ Code ran successfully but no output was printed.")
                st.write("Variables:", local_vars)
                passed, total = 1, 1

        except Exception as e:
            error_message = str(e)
            st.error(f"❌ Error: {error_message}")

            explanation, fix_hint, example = explain_error(error_message)
            if explanation:
                st.info(f"📘 Explanation: {explanation}")
                st.warning(f"💡 Hint: {fix_hint}")
                st.code(example, language="python")
            else:
                st.info("🤔 I don't recognize this error yet. API fallback coming soon.")
            passed, total = 0, 1

        finally:
            sys.stdout = old_stdout
            duration = int(time.time() - start_time)
            log_progress(username, "free_practice", passed, total, code, duration)