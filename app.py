import streamlit as st
from login import login_page
from register import register_page
from chat_utils import main_app, logout

# Initialize session state for login and user management
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None

# Add Bootstrap CSS
st.markdown("""
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
""", unsafe_allow_html=True)

# Main App Flow
if not st.session_state.logged_in:
    page = st.sidebar.radio("Choose an option", ["Login", "Register"])
    if page == "Login":
        login_page()
    elif page == "Register":
        register_page()
else:
    main_app()