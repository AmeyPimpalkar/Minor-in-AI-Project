# main.py
# Phase 1: Streamlit App Skeleton

import streamlit as st



# ---------------------------
# Temporary "database" for demo
# Later we can replace this with SQLite or JSON file
# ---------------------------
users_db = {}  # Stores {username: password}


# ---------------------------
# Function: Language Selection
# ---------------------------
def language_selection():
    st.subheader("Select a Programming Language to Learn")
    language = st.selectbox("Choose a language", ["Python (Available)", "Coming soon..."])

    if language.startswith("Python"):
        st.info("✅ Python selected! More features will load in Phase 2.")


# ---------------------------
# Main App Flow
# ---------------------------

from app import login as login_module
from app import coding as coding_module
from app import exercises as exercises_module

def main():
    st.title("💻 AI Learning Assistant (Prototype)")

    if "user" not in st.session_state:
        st.session_state["user"] = None

    # Sidebar menu
    if st.session_state["user"] is None:
        menu = ["Login", "Sign Up"]
    else:
        menu = ["Coding Practice", "Exercises", "Logout"]

    choice = st.sidebar.selectbox("Menu", menu)

    # Routes
    if choice == "Login":
        logged_in, user = login_module.login()
        if logged_in:
            st.session_state["user"] = user

    elif choice == "Sign Up":
        login_module.signup()

    elif choice == "Coding Practice" and st.session_state["user"]:
        coding_module.coding_practice()

    elif choice == "Exercises" and st.session_state["user"]:
        exercises_module.exercises()

    elif choice == "Logout":
        st.session_state["user"] = None
        st.info("👋 You have logged out.")

if __name__ == "__main__":
    main()

