import streamlit as st
import traceback
from core.error_handler import explain_error

def coding_practice():
    st.subheader("📝 Try Writing Python Code")

    code = st.text_area("Write your Python code here:", height=200)

    if st.button("Run Code"):
        try:
            # Run user code in a safe environment
            local_vars = {}
            exec(code, {}, local_vars)
            st.success("✅ Code ran successfully!")
            st.write("Output / Variables:", local_vars)

        except Exception as e:
            error_message = str(e)
            st.error(f"❌ Error: {error_message}")

            explanation, fix_hint, example = explain_error(error_message)
            if explanation:
                st.info(f"📘 Explanation: {explanation}")
                st.warning(f"💡 Hint: {fix_hint}")
                st.code(example, language="python")
            else:
                st.info("🤔 I don't recognize this error yet. Try asking the mentor (API mode coming soon).")