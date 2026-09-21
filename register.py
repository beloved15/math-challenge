"""
register.py
------------
Renders the registration screen and creates new user accounts.
"""

import streamlit as st
from utils import authentication as auth


def render():
    st.markdown("## 📝 Create Your Account")
    st.write("Join the Mathematics Quiz Challenge and start competing today!")

    with st.form("register_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("Username*", placeholder="Choose a username")
            email = st.text_input("Email*", placeholder="you@example.com")
            password = st.text_input("Password*", type="password", placeholder="At least 6 characters")
        with col2:
            full_name = st.text_input("Full Name*", placeholder="Your full name")
            phone = st.text_input("Phone Number*", placeholder="e.g. +1 555 123 4567")
            confirm_password = st.text_input("Confirm Password*", type="password", placeholder="Re-enter password")

        submitted = st.form_submit_button("✅ Register", use_container_width=True)

    if submitted:
        success, message = auth.register_user(
            username, full_name, email, phone, password, confirm_password
        )
        if success:
            st.success(f"🎉 {message}")
            st.session_state.auth_view = "login"
            st.balloons()
            st.rerun()
        else:
            st.error(f"❌ {message}")

    st.divider()
    if st.button("⬅️ Back to Login", use_container_width=True):
        st.session_state.auth_view = "login"
        st.rerun()
