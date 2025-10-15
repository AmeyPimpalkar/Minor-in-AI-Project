
import streamlit as st
import json
import os

CONCEPTS_DB = "data/concepts.json"

# Common Python errors to relevant concepts
ERROR_TO_CONCEPT = {
    "nameerror": "variable",
    "indexerror": "list",
    "keyerror": "dictionary",
    "attributeerror": "function",
    "logicerror": "loop",
    "syntaxerror": "syntax",
}

def load_concepts():
    if not os.path.exists(CONCEPTS_DB):
        return {}
    with open(CONCEPTS_DB, "r", encoding="utf-8") as f:
        return json.load(f)


data = load_concepts()
# Auto-open concept if redirected from coding practice
if "review_category" in st.session_state:
    preselect = st.session_state["review_category"]
    if preselect in data:
        st.success(f"📘 You recently faced an issue related to **{preselect.capitalize()}**. Let’s review it!")
        concept_key = preselect
    else:
        concept_key = st.selectbox("Choose a concept:", list(data.keys()))
else:
    concept_key = st.selectbox("Choose a concept:", list(data.keys()))

def concepts(username):
    st.header("📘 Learn Programming Concepts")

    # Detect redirect from coding practice
    review_target = st.session_state.get("review_category", None)
    if review_target:
        st.success(f"📖 Redirected from Coding Practice — Let’s review **{review_target.capitalize()}**")

    # Language selector
    language = st.selectbox("Select Language:", ["Python"], index=0)

    # Initialize familiarity per language
    if "familiarity" not in st.session_state:
        st.session_state["familiarity"] = {}

    # Ask familiarity only if not set
    if language not in st.session_state["familiarity"]:
        familiarity = st.radio(
            f"How familiar are you with {language}?",
            ["Beginner", "Intermediate", "Just Revising"],
            index=None,
            key=f"familiarity_{language}"
        )
        if familiarity:
            st.session_state["familiarity"][language] = familiarity

    familiarity = st.session_state["familiarity"].get(language)
    if not familiarity:
        st.info("Please select your familiarity level to continue.")
        return

    data = load_concepts()
    if not data:
        st.error("No concepts found in data/concepts.json")
        return

    # Auto-select concept if redirected from coding page
    auto_concept = None
    if review_target:
        key = ERROR_TO_CONCEPT.get(review_target.lower())
        if key and key in data:
            auto_concept = key

    # Search or dropdown
    search = st.text_input("🔍 Search for a concept (e.g., string, list, loop):").lower()
    concept_key = (
        auto_concept
        or (search if search in data else st.selectbox("Choose a concept:", list(data.keys())))
    )

    concept = data.get(concept_key)
    if not concept:
        st.warning("Concept not found.")
        return

    st.subheader(concept_key.capitalize())
    st.markdown(f"**Definition:** {concept.get('definition')}")

    # Explanations based on familiarity
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

    # Examples
    if concept.get("examples"):
        st.markdown("**Examples:**")
        for ex in concept["examples"]:
            st.code(ex, language=language.lower())

    # Real-life analogy
    if concept.get("real_life_analogy"):
        st.info(f"💡 Analogy: {concept['real_life_analogy']}")

    # Common mistakes
    if concept.get("common_mistakes"):
        st.markdown("⚠️ **Common Mistakes:**")
        for mistake in concept["common_mistakes"]:
            st.write(f"- {mistake}")

    # Mini project
    if concept.get("mini_project"):
        st.markdown("🎯 **Mini Project Idea:**")
        st.write(concept["mini_project"])

    # Quiz
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

    # Need more help
    if st.button("🤔 Need More Help?"):
        st.info("🔍 This feature will fetch simpler explanations and real-world examples from an external API. Coming soon!")

    st.markdown("---")
    st.caption(f"User: {username}")