"""
performance.py
---------------
"My Performance" page: personal analytics broken down by category and
difficulty, using Plotly charts.
"""

import streamlit as st
import plotly.express as px

from utils import database_manager as db
from utils import scoring


def render():
    st.markdown("## 📈 My Performance")

    results = db.get_user_results(st.session_state.username)
    if results.empty:
        st.info("No quiz data yet. Play a quiz to start building your performance stats! 🚀")
        return

    total_games = len(results)
    avg_percentage = round(results["Percentage"].mean(), 1)
    best_score = int(results["Score"].max())
    total_correct_pct_msg, _ = scoring.performance_message(avg_percentage)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🎮 Total Games", total_games)
    col2.metric("📊 Average Score", f"{avg_percentage}%")
    col3.metric("🏅 Best Single Score", best_score)
    col4.metric("🌟 Overall Level", total_correct_pct_msg)

    st.divider()

    tab1, tab2, tab3 = st.tabs(["📚 By Category", "⚡ By Difficulty", "📈 Trend"])

    with tab1:
        by_cat = results.groupby("Category")["Percentage"].mean().reset_index()
        by_cat["Percentage"] = by_cat["Percentage"].round(1)
        fig = px.bar(
            by_cat, x="Category", y="Percentage", color="Category",
            title="Average Score % by Category", text="Percentage",
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        order = ["Easy", "Intermediate", "Advanced"]
        by_diff = results.groupby("Difficulty_Level")["Percentage"].mean().reset_index()
        by_diff["Percentage"] = by_diff["Percentage"].round(1)
        by_diff["Difficulty_Level"] = by_diff["Difficulty_Level"].astype(
            "category"
        ).cat.set_categories(order, ordered=True)
        by_diff = by_diff.sort_values("Difficulty_Level")
        fig = px.bar(
            by_diff, x="Difficulty_Level", y="Percentage", color="Difficulty_Level",
            title="Average Score % by Difficulty", text="Percentage",
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        trend = results.sort_values("Date_Played")
        fig = px.line(
            trend, x="Date_Played", y="Percentage", markers=True,
            title="Score Trend Over Time",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.markdown("### 🥧 Games Played by Category")
    cat_counts = results["Category"].value_counts().reset_index()
    cat_counts.columns = ["Category", "Games"]
    fig_pie = px.pie(cat_counts, names="Category", values="Games", hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)
