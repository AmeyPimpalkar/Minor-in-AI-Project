import streamlit as st
import json
import os
import time

CONCEPTS_DB = "data/concepts.json"
REVISE_DB = "data/revise_concepts.json"

# Map common Python errors to key concepts
ERROR_TO_CONCEPT = {
    "NameError": "variable", 
    "IndexError": "list",
    "KeyError": "dictionary",
    "AttributeError": "function", 
    "LogicError": "loop",
    "SyntaxError": "syntax",
    "TypeError": "variable",
    "ValueError": "variable",
    "IndentationError": "syntax",
    "ModuleNotFoundError": "syntax"
}


def load_json(path):
    """Load JSON safely."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def concepts(username):
    """Main page for learning concepts."""
    st.header("📘 Learn Programming Concepts")

    # Load both databases
    data = load_json(CONCEPTS_DB)
    revise_data = load_json(REVISE_DB)

    if not data:
        st.error("No concepts found in data/concepts.json")
        return

    # Check if user recently clicked "Review Related Concept"
    recent_path = "data/revise_concepts.json"
    concept_key = None

    if os.path.exists(recent_path):
        with open(recent_path, "r", encoding="utf-8") as f:
            try:
                last_review = json.load(f).get("last_review", {})
                if time.time() - last_review.get("timestamp", 0) < 120:
                    key = last_review.get("category", "")
                    if key in revise_data:
                        st.success(f"📘 Revisiting **{key.capitalize()}** as you requested earlier.")
                        concept_key = key
            except Exception:
                pass

    # If no recent concept, let user choose manually
    if not concept_key:
        search = st.text_input("🔍 Search for a concept (e.g., string, list, loop):", key="search_concept").lower()
        concept_key = (
            search if search in data else st.selectbox("Choose a concept:", list(data.keys()), key="concept_select")
        )

    # Decide which dataset to pull from (prefer revise if available)
    concept = revise_data.get(concept_key, data.get(concept_key))
    if not concept:
        st.warning("Concept not found.")
        return

    # Familiarity section
    language = st.selectbox("Select Language:", ["Python"], index=0, key="lang_select")
    if "familiarity" not in st.session_state:
        st.session_state["familiarity"] = {}
    if language not in st.session_state["familiarity"]:
        familiarity = st.radio(
            f"How familiar are you with {language}?",
            ["Beginner", "Intermediate", "Just Revising"],
            index=0,
            key=f"fam_{language}"
        )
        if familiarity:
            st.session_state["familiarity"][language] = familiarity

    familiarity = st.session_state["familiarity"].get(language)
    if not familiarity:
        st.info("Please select your familiarity level to continue.")
        return

    # Display content
    st.subheader(concept_key.capitalize())
    st.markdown(f"**Definition:** {concept.get('definition', 'No definition available.')}")

    # Explanations by familiarity
    if "beginner_explanation" in concept or "intermediate_explanation" in concept:
        if familiarity == "Beginner":
            with st.expander("👶 Beginner Explanation", expanded=True):
                st.write(concept.get("beginner_explanation", concept.get("definition", "")))
        elif familiarity == "Intermediate":
            with st.expander("⚡ Intermediate Explanation", expanded=True):
                st.write(concept.get("intermediate_explanation", concept.get("definition", "")))
        else:
            st.warning("Skipping explanations, let’s test your knowledge!")
            with st.expander("Explanation", expanded=True):
                st.write(concept.get("intermediate_explanation", concept.get("definition", "")))

    # Examples
    if concept.get("example"):
        st.markdown("**Example:**")
        st.code(concept["example"], language="python")
    elif concept.get("examples"):
        st.markdown("**Examples:**")
        for ex in concept["examples"]:
            st.code(ex, language="python")

    # Real-life analogy
    if concept.get("analogy"):
        st.info(f"💡 Analogy: {concept['analogy']}")
    elif concept.get("real_life_analogy"):
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

    if st.button("🤔 Need More Help?", key="help_btn"):
        st.info("🔍 This feature will fetch simpler explanations and real-world examples from an external API. Coming soon!")

    st.markdown("---")
    st.caption(f"User: {username}")