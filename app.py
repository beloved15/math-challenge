"""
app.py
------
Mathematics Quiz Challenge App — main entry point.

This file wires together authentication state, the sidebar navigation,
and every page module under pages/. It intentionally does NOT use
Streamlit's native multipage `pages/` auto-discovery, because that
mechanism reruns each page as an independent script and makes it much
harder to consistently gate every screen behind login/session state.
Instead, pages/*.py expose a `render()` function that this file calls
based on `st.session_state.current_page`, giving us a single source of
truth for auth + navigation.
"""

import streamlit as st

from utils import database_manager as db
from utils import question_generator

from pages import login, register, dashboard, quiz, leaderboard, profile, performance, admin

# --------------------------------------------------------------------------
# Page configuration
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Mathematics Quiz Challenge",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------
# One-time startup: make sure the Excel database exists and is seeded.
# --------------------------------------------------------------------------
db.ensure_database_exists()
if "seeded" not in st.session_state:
    question_generator.seed_sample_questions()
    st.session_state.seeded = True

# --------------------------------------------------------------------------
# Session state defaults
# --------------------------------------------------------------------------
defaults = {
    "logged_in": False,
    "username": None,
    "full_name": None,
    "auth_view": "login",          # "login" | "register" | "admin"
    "admin_logged_in": False,
    "current_page": "Dashboard",
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# --------------------------------------------------------------------------
# Minor custom styling
# --------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
    }
    div[data-testid="stMetric"] {
        background-color: rgba(120, 120, 120, 0.08);
        border-radius: 12px;
        padding: 12px;
    }

    /*Hide Streamlit's automatic page navigation */
    [data-testid = "stSidebarNav"] {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# Sidebar + routing
# --------------------------------------------------------------------------
NAV_ITEMS = [
    ("Dashboard", "🏠"),
    ("Start Quiz", "🧮"),
    ("My Performance", "📈"),
    ("Leaderboard", "🏆"),
    ("Profile", "👤"),
]

def render_sidebar():
    with st.sidebar:
        st.markdown("# 🧮 Math Quiz Challenge")

        if st.session_state.admin_logged_in:
            st.success("🛠️ Admin Mode")
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.admin_logged_in = False
                st.session_state.auth_view = "login"
                st.rerun()
            return

        if st.session_state.logged_in:
            st.success(f"👋 {st.session_state.full_name}")
            st.caption(f"@{st.session_state.username}")
            st.divider()

            for label, icon in NAV_ITEMS:
                is_active = st.session_state.current_page == label
                if st.button(
                    f"{icon} {label}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                    key=f"nav_{label}",
                ):
                    st.session_state.current_page = label
                    # Leaving the quiz page mid-game resets it cleanly.
                    if label != "Start Quiz":
                        st.session_state.quiz_stage = "setup"
                    st.rerun()

            st.divider()
            if st.button("🚪 Logout", use_container_width=True):
                for key in ["logged_in", "username", "full_name"]:
                    st.session_state[key] = defaults[key]
                st.session_state.current_page = "Dashboard"
                st.session_state.auth_view = "login"
                st.rerun()
        else:
            st.caption("Please log in or register to play.")


def render_main():
    if st.session_state.admin_logged_in:
        admin.render()
        return

    if not st.session_state.logged_in:
        if st.session_state.auth_view == "register":
            register.render()
        elif st.session_state.auth_view == "admin":
            admin.render_login()
        else:
            login.render()
        return

    page = st.session_state.current_page
    if page == "Dashboard":
        dashboard.render()
    elif page == "Start Quiz":
        quiz.render()
    elif page == "My Performance":
        performance.render()
    elif page == "Leaderboard":
        leaderboard.render()
    elif page == "Profile":
        profile.render()
    else:
        dashboard.render()

render_sidebar()
render_main()