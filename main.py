# main.py
# Phase 1: Streamlit App Skeleton

import streamlit as st

# ---------------------------
# Temporary "database" for demo
# Later we can replace this with SQLite or JSON file
# ---------------------------
users_db = {}  # Stores {username: password}


# ---------------------------
# Function: Sign Up
# ---------------------------
def signup():
    st.subheader("Create a New Account")
    new_user = st.text_input("Choose a username")
    new_pass = st.text_input("Choose a password", type="password")

    if st.button("Sign Up"):
        if new_user in users_db:
            st.warning("Username already exists. Try another one.")
        else:
            users_db[new_user] = new_pass
            st.success("Account created successfully! Please log in now.")


# ---------------------------
# Function: Login
# ---------------------------
def login():
    st.subheader("Login to Your Account")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in users_db and users_db[username] == password:
            st.success(f"Welcome {username}!")
            # After login → go to language selection
            language_selection()
        else:
            st.error("Invalid username or password.")


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
        login()
    elif choice == "Sign Up":
        signup()


if __name__ == "__main__":
    main()