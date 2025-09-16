# main.py
# Phase 1: Streamlit App Skeleton

import streamlit as st
from app import login as login_module

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

def main():
    st.title("💻 AI Learning Assistant (Prototype)")

    menu = ["Login", "Sign Up"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Login":
        logged_in, user = login_module.login()
        if logged_in:
            st.session_state["user"] = user
            st.info("🔜 Next step: load language selection here...")
    elif choice == "Sign Up":
        login_module.signup()


if __name__ == "__main__":
    main()

