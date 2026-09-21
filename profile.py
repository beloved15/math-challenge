"""
profile.py
----------
User profile page: view account details and personal quiz history/stats.
"""

import streamlit as st
import plotly.express as px

from utils import database_manager as db


def render():
    st.markdown("## 👤 My Profile")
    user = db.get_user(st.session_state.username)
    if user is None:
        st.error("Could not load your profile.")
        return

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"### 🎓 {user['Current_Level']}")
        st.metric("🎮 Games Played", int(user["Total_Games_Played"]))
        st.metric("📊 Average Score", f"{user['Average_Percentage']}%")
        st.metric("🏆 Total Score", int(user["Total_Score"]))

    with col2:
        st.markdown("#### Account Details")
        st.write(f"**Username:** {user['Username']}")
        st.write(f"**Full Name:** {user['Full_Name']}")
        st.write(f"**Email:** {user['Email']}")
        st.write(f"**Phone Number:** {user['Phone_Number']}")
        st.write(f"**Member Since:** {user['Registration_Date']}")

    st.divider()
    st.markdown("### 📜 Recent Quiz History")
    results = db.get_user_results(st.session_state.username).sort_values(
        "Date_Played", ascending=False
    )
    if results.empty:
        st.info("You haven't played any quizzes yet. Head to **Start Quiz** to begin! 🚀")
        return

    st.dataframe(
        results[[
            "Date_Played", "Category", "Difficulty_Level",
            "Number_of_Questions", "Score", "Percentage", "Time_Taken",
        ]].head(20),
        use_container_width=True, hide_index=True,
    )

    if len(results) >= 2:
        chart_df = results.sort_values("Date_Played").tail(20)
        fig = px.line(
            chart_df, x="Date_Played", y="Percentage", markers=True,
            title="Your Score Trend (Most Recent Games)",
        )
        st.plotly_chart(fig, use_container_width=True)
