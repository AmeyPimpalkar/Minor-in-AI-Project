
# Temporary "database" for demo
# Later we can replace this with SQLite or JSON file
users_db = {}  # Stores {username: password}


# Language Selection 
# More languages coming in future

def language_selection():
    st.subheader("Select a Programming Language to Learn")
    language = st.selectbox("Choose a language", ["Python (Available)", "Coming soon..."])

    if language.startswith("Python"):
        st.info("✅ Python selected! More features will load in Phase 2.")


# Main
import streamlit as st
from app import login as login_module
from app import coding as coding_module
from app import exercises as exercises_module
from app import dashboard as dashboard_module
from app import concepts as concepts_module


def main():
    st.set_page_config(page_title="AI Coding Mentor", layout="wide")
    st.title("🤖 AI Coding Mentor")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user = None

    if not st.session_state.logged_in:
        logged_in, user = login_module.login()
        if logged_in:
            st.session_state.logged_in = True
            st.session_state.user = user
    else:
        st.sidebar.success(f"👋 Welcome, {st.session_state.user}")
        choice = st.sidebar.radio(
            "Navigation",
            ["Dashboard", "Concepts","Coding Practice", "Exercises", "Logout"]
        )

        if choice == "Coding Practice":
            coding_module.coding_practice(st.session_state.user)
        elif choice == "Exercises":
            exercises_module.exercises(st.session_state.user)
        elif choice == "Dashboard":
            dashboard_module.dashboard(st.session_state.user)
        elif choice == "Concepts":
            concepts_module.concepts(st.session_state.user)
        elif choice == "Logout":
            st.session_state.logged_in = False
            st.session_state.user = None
            st.sidebar.info("Logged out successfully!")
        elif choice == "dashboard":
            dashboard_module.dashboard(st.session_state.user)


if __name__ == "__main__":
    main()

