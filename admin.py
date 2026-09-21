"""
admin.py
--------
Admin dashboard: separate admin login, question management (CRUD),
user management, and Plotly-powered performance analytics.
"""

import streamlit as st

from utils import authentication as auth
from utils import database_manager as db
from utils import analytics


# --------------------------------------------------------------------------
# Admin login
# --------------------------------------------------------------------------
def render_login():
    st.markdown("## 🛠️ Admin Login")
    st.caption("Restricted area for application administrators.")

    with st.form("admin_login_form"):
        username = st.text_input("Admin Username")
        password = st.text_input("Admin Password", type="password")
        submitted = st.form_submit_button("🔓 Login as Admin", use_container_width=True)

    if submitted:
        success, message = auth.login_admin(username, password)
        if success:
            st.session_state.admin_logged_in = True
            st.success(message)
            st.rerun()
        else:
            st.error(f"❌ {message}")

    st.divider()
    if st.button("⬅️ Back to Login"):
        st.session_state.auth_view = "login"
        st.rerun()


# --------------------------------------------------------------------------
# Question management
# --------------------------------------------------------------------------
def _render_question_management():
    st.markdown("### ❓ Question Management")

    with st.expander("➕ Add a New Question"):
        with st.form("add_question_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                category = st.selectbox("Category", [c for c in db.CATEGORIES if c != "Mixture"])
            with col2:
                difficulty = st.selectbox("Difficulty", db.DIFFICULTIES)

            text = st.text_area("Question Text")
            col3, col4 = st.columns(2)
            with col3:
                option_a = st.text_input("Option A")
                option_c = st.text_input("Option C")
            with col4:
                option_b = st.text_input("Option B")
                option_d = st.text_input("Option D")

            correct = st.selectbox("Correct Answer", ["A", "B", "C", "D"])
            explanation = st.text_area("Explanation (shown after answering)")

            add_submitted = st.form_submit_button("✅ Add Question", use_container_width=True)

        if add_submitted:
            if not text or not option_a or not option_b or not option_c or not option_d:
                st.error("Please fill in the question text and all four options.")
            else:
                db.add_question(category, difficulty, text, option_a, option_b, option_c, option_d, correct, explanation)
                st.success("Question added successfully! ✅")
                st.rerun()

    st.divider()
    st.markdown("#### 📋 Existing Questions")

    col1, col2 = st.columns(2)
    with col1:
        filter_category = st.selectbox("Filter by Category", ["All"] + [c for c in db.CATEGORIES if c != "Mixture"])
    with col2:
        filter_difficulty = st.selectbox("Filter by Difficulty", ["All"] + db.DIFFICULTIES)

    questions = db.load_questions()
    if filter_category != "All":
        questions = questions[questions["Category"] == filter_category]
    if filter_difficulty != "All":
        questions = questions[questions["Difficulty_Level"] == filter_difficulty]

    st.caption(f"Showing {len(questions)} question(s).")

    for _, q in questions.iterrows():
        with st.expander(f"[{q['Question_ID']}] {q['Category']} / {q['Difficulty_Level']} — {q['Question_Text'][:60]}"):
            with st.form(f"edit_form_{q['Question_ID']}"):
                text = st.text_area("Question Text", value=q["Question_Text"], key=f"text_{q['Question_ID']}")
                col_a, col_b = st.columns(2)
                with col_a:
                    option_a = st.text_input("Option A", value=q["Option_A"], key=f"a_{q['Question_ID']}")
                    option_c = st.text_input("Option C", value=q["Option_C"], key=f"c_{q['Question_ID']}")
                with col_b:
                    option_b = st.text_input("Option B", value=q["Option_B"], key=f"b_{q['Question_ID']}")
                    option_d = st.text_input("Option D", value=q["Option_D"], key=f"d_{q['Question_ID']}")
                correct = st.selectbox(
                    "Correct Answer", ["A", "B", "C", "D"],
                    index=["A", "B", "C", "D"].index(q["Correct_Answer"]) if q["Correct_Answer"] in ["A", "B", "C", "D"] else 0,
                    key=f"correct_{q['Question_ID']}",
                )
                explanation = st.text_area("Explanation", value=q.get("Explanation", ""), key=f"exp_{q['Question_ID']}")

                col_save, col_delete = st.columns(2)
                with col_save:
                    save = st.form_submit_button("💾 Save Changes", use_container_width=True)
                with col_delete:
                    delete = st.form_submit_button("🗑️ Delete Question", use_container_width=True)

            if save:
                db.update_question(int(q["Question_ID"]), {
                    "Question_Text": text, "Option_A": option_a, "Option_B": option_b,
                    "Option_C": option_c, "Option_D": option_d,
                    "Correct_Answer": correct, "Explanation": explanation,
                })
                st.success("Updated! ✅")
                st.rerun()
            if delete:
                db.delete_question(int(q["Question_ID"]))
                st.warning("Question deleted.")
                st.rerun()


# --------------------------------------------------------------------------
# User management
# --------------------------------------------------------------------------
def _render_user_management():
    st.markdown("### 👥 User Management")
    users = db.load_users()

    search = st.text_input("🔍 Search users by username or email")
    if search:
        mask = (
            users["Username"].astype(str).str.contains(search, case=False, na=False)
            | users["Email"].astype(str).str.contains(search, case=False, na=False)
        )
        users = users[mask]

    st.caption(f"{len(users)} user(s) found.")
    st.dataframe(
        users[[
            "Username", "Full_Name", "Email", "Phone_Number", "Registration_Date",
            "Total_Games_Played", "Total_Score", "Average_Percentage", "Current_Level",
        ]],
        use_container_width=True, hide_index=True,
    )

    st.divider()
    st.markdown("#### 🔎 Individual User Stats")
    if not users.empty:
        selected = st.selectbox("Select a user", users["Username"].tolist())
        user_results = db.get_user_results(selected)
        if user_results.empty:
            st.info("This user hasn't played any quizzes yet.")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Games Played", len(user_results))
            col2.metric("Average %", f"{round(user_results['Percentage'].mean(), 1)}%")
            col3.metric("Best Score", int(user_results["Score"].max()))
            st.dataframe(user_results, use_container_width=True, hide_index=True)


# --------------------------------------------------------------------------
# Analytics
# --------------------------------------------------------------------------
def _render_analytics():
    st.markdown("### 📊 Performance Analytics")

    users = db.load_users()
    results = db.load_results()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Registered Users", len(users))
    col2.metric("🎮 Quizzes Completed", len(results))
    col3.metric(
        "📊 Average Score",
        f"{round(results['Percentage'].mean(), 1)}%" if not results.empty else "N/A",
    )
    col4.metric(
        "⭐ Most Popular Category", analytics.most_popular_category(results),
    )
    st.metric("🧩 Most Difficult Category", analytics.most_difficult_category(results))

    if results.empty:
        st.info("No quiz results yet — analytics will populate once users start playing.")
        return

    st.divider()
    tab1, tab2, tab3 = st.tabs(["📊 Category Breakdown", "⚡ Difficulty Breakdown", "📈 Trends"])

    with tab1:
        fig_bar = analytics.quizzes_by_category_bar(results)
        if fig_bar:
            st.plotly_chart(fig_bar, use_container_width=True)
        fig_pie = analytics.category_popularity_pie(results)
        if fig_pie:
            st.plotly_chart(fig_pie, use_container_width=True)
        fig_avg = analytics.average_score_by_category_bar(results)
        if fig_avg:
            st.plotly_chart(fig_avg, use_container_width=True)

    with tab2:
        fig_diff = analytics.average_score_by_difficulty_bar(results)
        if fig_diff:
            st.plotly_chart(fig_diff, use_container_width=True)

    with tab3:
        fig_trend = analytics.performance_trend_line(results)
        if fig_trend:
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Not enough dated data yet to plot a trend.")


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------
def render():
    if not st.session_state.get("admin_logged_in", False):
        render_login()
        return

    st.markdown("# 🛠️ Admin Dashboard")
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("🚪 Logout"):
            st.session_state.admin_logged_in = False
            st.session_state.auth_view = "login"
            st.rerun()

    tab1, tab2, tab3 = st.tabs(["❓ Questions", "👥 Users", "📊 Analytics"])
    with tab1:
        _render_question_management()
    with tab2:
        _render_user_management()
    with tab3:
        _render_analytics()
