"""
leaderboard.py
---------------
Weekly leaderboard view: ranking, search, current-user highlight,
weekly-winner announcement, and a "Contact Admin on WhatsApp" reward button.
"""

import urllib.parse
import streamlit as st

from utils import database_manager as db

# Configurable admin WhatsApp number (include country code, digits only).
ADMIN_WHATSAPP_NUMBER = "+2349053521354"


def _whatsapp_link(message: str) -> str:
    encoded = urllib.parse.quote(message)
    return f"https://wa.me/{ADMIN_WHATSAPP_NUMBER}?text={encoded}"


def render():
    st.markdown("## 🏆 Weekly Leaderboard")
    st.caption("Rankings reset every week based on total score from quizzes played in the last 7 days.")

    if st.button("🔄 Refresh Leaderboard"):
        db.rebuild_leaderboard()
        st.rerun()

    leaderboard = db.rebuild_leaderboard()

    if leaderboard.empty:
        st.info("No quiz activity yet this week. Be the first to play and claim the top spot! 🚀")
        return

    winner = leaderboard.sort_values("Rank").iloc[0]
    st.success(
        f" **{winner['Username']}** is this week's #1 ranked "
        f"player with a score of **{int(winner['Weekly_Score'])}**!"
    )

    st.divider()

    search = st.text_input("🔍 Search leaderboard by username", placeholder="Type a username...")
    display_df = leaderboard.copy()
    if search:
        display_df = display_df[display_df["Username"].str.contains(search, case=False, na=False)]

    current_user = st.session_state.get("username", "")
    st.markdown("### 📋 Rankings")

    for _, row in display_df.iterrows():
        rank = int(row["Rank"])
        is_me = row["Username"].lower() == current_user.lower()
        is_winner = rank == 1
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"#{rank}")

        cols = st.columns([1, 3, 2, 2, 2])
        style = "**" if is_me else ""
        cols[0].markdown(f"### {medal}")
        cols[1].markdown(f"{style}{row['Username']}{style}" + (" 👤 (You)" if is_me else ""))
        cols[2].markdown(f"Score: **{int(row['Weekly_Score'])}**")
        cols[3].markdown(f"Avg: {row['Average_Percentage']}%")
        cols[4].markdown(f"Games: {int(row['Games_Played'])}")
        if is_winner:
            st.caption("👑 Weekly Champion")
        st.divider()

    # Highlight current user's position even if filtered out of the search.
    my_row = leaderboard[leaderboard["Username"].str.lower() == current_user.lower()]
    if not my_row.empty:
        st.info(f"📍 Your current rank this week: **#{int(my_row.iloc[0]['Rank'])}**")
    else:
        st.info("📍 You haven't played a quiz this week yet — play one to join the rankings!")
