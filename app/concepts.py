# app/concepts.py
import streamlit as st
import json
import os

CONCEPTS_DB = "data/concepts.json"



def load_concepts():
    if not os.path.exists(CONCEPTS_DB):
        return {}
    with open(CONCEPTS_DB, "r", encoding="utf-8") as f:
        return json.load(f)

def concepts(username):
    st.header("📘 Learn Python Concepts")

    data = load_concepts()
    if not data:
        st.error("No concepts found in data/concepts.json")
        return

    # 🔹 Search option
    search = st.text_input("🔍 Search for a concept (e.g., string, list, loop):").lower()

    if search and search in data:
        concept_key = search
    else:
        # Dropdown if no search
        concept_key = st.selectbox("Choose a concept:", list(data.keys()))

    concept = data[concept_key]

    st.subheader(concept_key.capitalize())
    st.markdown(f"**Definition:** {concept.get('definition')}")

    with st.expander("👶 Beginner Explanation"):
        st.write(concept.get("beginner_explanation"))

    with st.expander("⚡ Intermediate Explanation"):
        st.write(concept.get("intermediate_explanation"))

    if concept.get("examples"):
        st.markdown("**Examples:**")
        for ex in concept["examples"]:
            st.code(ex, language="python")

    if concept.get("real_life_analogy"):
        st.info(f"💡 Analogy: {concept['real_life_analogy']}")

    if concept.get("common_mistakes"):
        st.markdown("⚠️ **Common Mistakes:**")
        for mistake in concept["common_mistakes"]:
            st.write(f"- {mistake}")

    if concept.get("mini_project"):
        st.markdown("🎯 **Mini Project Idea:**")
        st.write(concept["mini_project"])

    # Quiz section
    if concept.get("quiz_questions"):
        st.subheader("📝 Quick Quiz")
        for i, q in enumerate(concept["quiz_questions"], 1):
            st.write(f"**Q{i}. {q['question']}**")
            choice = st.radio("Choose an answer:", q["options"], key=f"{concept_key}_{i}")
            if st.button(f"Check Answer {i}", key=f"btn_{concept_key}_{i}"):
                if choice.startswith(q["answer"]):
                    st.success("✅ Correct!")
                else:
                    st.error(f"❌ Wrong! Correct answer is: {q['answer']}")

    # Future: add "Explain Better" button → API fallback
    st.markdown("---")
    st.caption(f"User: {username}")