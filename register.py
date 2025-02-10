import streamlit as st
from chat_utils import load_user_data, save_user_data

# Registration Page
def register_page():
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

    st.title("Register")
    new_username = st.text_input("New Username")
    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    if st.button("Register", key="register"):
        if new_password != confirm_password:
            st.error("Passwords do not match.")
        elif not new_username or not new_password:
            st.error("Username and password cannot be empty.")
        else:
            user_data = load_user_data()
            if new_username in user_data:
                st.error("Username already exists.")
            else:
                user_data[new_username] = new_password
                save_user_data(user_data)
                st.success("Registration successful! Please log in.")
                st.rerun()