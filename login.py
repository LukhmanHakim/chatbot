import streamlit as st
from chat_utils import load_user_data

# Login Page
def login_page():
    st.markdown("""
    <nav class="navbar navbar-expand-lg navbar-light bg-light">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">Jom Besut ChatBox</a>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="#" onclick="document.getElementById('login').click()">Login</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#" onclick="document.getElementById('register').click()">Register</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>
    """, unsafe_allow_html=True)

    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login", key="login"):
        user_data = load_user_data()
        if username in user_data and user_data[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"Welcome back, {username}!")
            st.rerun()
        else:
            st.error("Invalid username or password.")