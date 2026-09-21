"""
login.py
--------
Renders the login screen and handles authenticating a user into session_state.
"""

import streamlit as st
import authentication as auth


def render():
    st.subheader("Math Quiz Challenge")
    st.write("...test your Speed and Accuracy!")

    st.divider()

    st.markdown("## 🔐 Login to Your Account")
    st.write("Welcome back! Enter your credentials to continue your math journey.")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submitted = st.form_submit_button("🚀 Login", use_container_width=True)

    if submitted:
        success, message, user = auth.login_user(username, password)
        if success:
            st.session_state.logged_in = True
            st.session_state.username = user["Username"]
            st.session_state.full_name = user["Full_Name"]
            st.session_state.current_page = "Dashboard"
            st.success(message)
            st.rerun()
        else:
            st.error(f"❌ {message}")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 Create a new account", use_container_width=True):
            st.session_state.auth_view = "register"
            st.rerun()
    with col2:
        if st.button("🛠️ Admin Login", use_container_width=True):
            st.session_state.auth_view = "admin"
            st.rerun()
