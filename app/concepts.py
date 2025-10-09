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
    st.header("📘 Learn Programming Concepts")

    # Language selector (default to Python)
    language = st.selectbox("Select Language:", ["Python"], index=0)

    # Initialize familiarity per language in session_state
    if "familiarity" not in st.session_state:
        st.session_state["familiarity"] = {}

    # Ask familiarity only if not set
    if language not in st.session_state["familiarity"]:
        familiarity = st.radio(
            f"How familiar are you with {language}?",
            ["Beginner", "Intermediate", "Just Revising"],
            index=None,  # no default pre-selected option
            key=f"familiarity_{language}"
        )
        if familiarity:
            st.session_state["familiarity"][language] = familiarity

    # Show reset button
    if st.button("🔄 Reset Familiarity"):
        if "familiarity" in st.session_state and language in st.session_state["familiarity"]:
            del st.session_state["familiarity"][language]
            st.success(f"Reset familiarity for {language}. Please reselect.")

    # Ensure familiarity is defined
    familiarity = st.session_state["familiarity"].get(language)
    if not familiarity:
        st.info("Please select your familiarity level to continue.")
        return

    data = load_concepts()
    if not data:
        st.error("No concepts found in data/concepts.json")
        return

    # Search option
    search = st.text_input("🔍 Search for a concept (e.g., string, list, loop):").lower()

    if search and search in data:
        concept_key = search
    else:
        concept_key = st.selectbox("Choose a concept:", list(data.keys()))

    concept = data[concept_key]

    st.subheader(concept_key.capitalize())
    st.markdown(f"**Definition:** {concept.get('definition')}")

    # Show explanations based on familiarity
    if familiarity == "Beginner":
        with st.expander("👶 Beginner Explanation", expanded=True):
            st.write(concept.get("beginner_explanation"))

    elif familiarity == "Intermediate":
        with st.expander("⚡ Intermediate Explanation", expanded=True):
            st.write(concept.get("intermediate_explanation"))

    elif familiarity == "Just Revising":
        st.warning("Skipping explanations, let’s test your knowledge!")
        with st.expander("Explanation", expanded=True):
            st.write(concept.get("intermediate_explanation"))

    if concept.get("examples"):
        st.markdown("**Examples:**")
        for ex in concept["examples"]:
            st.code(ex, language=language.lower())

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

    # “Need more help” button
    if st.button("🤔 Need More Help?"):
        st.info("🔍 This feature will fetch simpler explanations and real-world examples from an external API. Coming soon!")

    st.markdown("---")
    st.caption(f"User: {username}")