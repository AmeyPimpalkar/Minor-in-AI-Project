import streamlit as st
from core.error_handler import explain_error

st.title("🧠 AI Error Classifier Tester")

st.write("Enter an error message below and see how the AI classifies it!")

# Text area for user input
user_input = st.text_area("🔍 Paste or type your Python error message here:", height=150)

if st.button("Analyze Error"):
    if user_input.strip():
        with st.spinner("Analyzing using AI model..."):
            explanation, fix_hint, example = explain_error(user_input)
            
            if explanation:
                st.success("✅ AI Model successfully classified the error!")
                st.markdown(f"**Prediction:** {explanation}")
                st.markdown(f"**Suggested Fix:** {fix_hint}")
                if example:
                    st.markdown(f"**Example:** {example}")
            else:
                st.warning(fix_hint or "Could not classify this error. Try again.")
    else:
        st.info("Please enter an error message to analyze.")