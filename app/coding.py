import streamlit as st
import traceback
from io import StringIO
import sys
from core.error_handler import explain_error

def coding_practice():
    st.subheader("📝 Try Writing Python Code")

    code = st.text_area("Write your Python code here:", height=200)

    if st.button("Run Code"):
        # Redirect print() output to a buffer
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()

        try:
            local_vars = {}
            exec(code, {}, local_vars)  # run user code
            output = mystdout.getvalue()  # capture print() output

            if output.strip():
                st.success("✅ Code ran successfully!")
                st.text("📤 Output:")
                st.code(output, language="text")
            else:
                st.success("✅ Code ran successfully but no output was printed.")
                st.write("Variables:", local_vars)

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

        finally:
            # Reset stdout
            sys.stdout = old_stdout