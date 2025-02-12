import streamlit as st
from chat_utils import load_user_data

# Login Page
def login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user_data = load_user_data()
        if username in user_data and user_data[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"Welcome back, {username}!")
            st.rerun()
        else:
            st.error("Invalid username and password.")