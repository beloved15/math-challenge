"""
dashboard.py
------------
The landing page users see right after logging in: a friendly overview
of their stats plus quick-launch cards for the rest of the app.
"""

import streamlit as st

import database_manager as db


def render():
    st.markdown(f"## 👋 Welcome back, {st.session_state.get('full_name', st.session_state.username)}!")

    user = db.get_user(st.session_state.username)
    if user is not None:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🎮 Games Played", int(user["Total_Games_Played"]))
        col2.metric("🏆 Total Score", int(user["Total_Score"]))
        col3.metric("📊 Average Score", f"{user['Average_Percentage']}%")
        col4.metric("🎓 Level", user["Current_Level"])

    st.divider()
    st.markdown("### 🚀 Quick Actions")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### 🧮 Start a Quiz")
        st.write("Test your skills across 7 categories and 3 difficulty levels.")
        if st.button("Play Now ▶️", use_container_width=True, key="dash_play"):
            st.session_state.current_page = "Start Quiz"
            st.rerun()

    with col2:
        st.markdown("#### 🏆 Leaderboard")
        st.write("See how you rank against other players this week.")
        if st.button("View Rankings 🏅", use_container_width=True, key="dash_lb"):
            st.session_state.current_page = "Leaderboard"
            st.rerun()

    with col3:
        st.markdown("#### 📈 My Performance")
        st.write("Dive into your personal stats and trends.")
        if st.button("View Stats 📊", use_container_width=True, key="dash_perf"):
            st.session_state.current_page = "My Performance"
            st.rerun()

    st.divider()
    st.markdown("### 🧭 Available Categories")
    cats = [c for c in db.CATEGORIES]
    cols = st.columns(4)
    icons = {
        "Addition": "➕", "Subtraction": "➖", "Multiplication": "✖️",
        "Division": "➗", "Algebra": "🔤", "Statistics": "📊", "Mixture": "🎲",
    }
    for i, cat in enumerate(cats):
        with cols[i % 4]:
            st.markdown(f"**{icons.get(cat, '📘')} {cat}**")
