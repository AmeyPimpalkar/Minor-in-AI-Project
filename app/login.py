import streamlit as st
import json
import os

# Path to the user database
USER_DB = "db/users.json"


def load_users():
    """Load users from JSON file, or return empty dict if file is empty/invalid."""
    if os.path.exists(USER_DB):
        try:
            with open(USER_DB, "r") as f:
                content = f.read().strip()
                if not content:  # if file is empty
                    return {}
                return json.loads(content)
        except json.JSONDecodeError:
            return {}
    return {}


def save_users(users):
    """Save users dictionary into JSON file."""
    with open(USER_DB, "w") as f:
        json.dump(users, f, indent=4)



# Sign Up function
def signup():
    st.subheader("Create a New Account")
    new_user = st.text_input("Choose a username")
    new_pass = st.text_input("Choose a password", type="password")

    if st.button("Sign Up"):
        users = load_users()
        if new_user in users:
            st.warning("⚠️ Username already exists. Try another one.")
        elif not new_user or not new_pass:
            st.error("Username and password cannot be empty.")
        else:
            users[new_user] = {"password": new_pass}
            save_users(users)
            st.success("✅ Account created successfully! Please log in now.")



# Login function
def login():
    st.subheader("Login to Your Account")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        users = load_users()
        if username in users and users[username]["password"] == password:
            st.success(f"🎉 Welcome {username}!")
            return True, username
        else:
            st.error("❌ Invalid username or password.")
            return False, None

    return False, None