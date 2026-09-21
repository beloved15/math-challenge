"""
quiz.py
-------
The quiz-taking flow: category/difficulty/question-count setup, the
question-by-question game screen (with a 20-second countdown timer per
question), and the final results summary.
"""

import time
import streamlit as st

import database_manager as db
import scoring
import timer


# --------------------------------------------------------------------------
# State management helpers
# --------------------------------------------------------------------------
def _reset_quiz_state():
    st.session_state.quiz_stage = "setup"
    st.session_state.quiz_questions = None
    st.session_state.quiz_index = 0
    st.session_state.quiz_correct = 0
    st.session_state.quiz_wrong = 0
    st.session_state.quiz_answers = []
    st.session_state.answered_current = False
    st.session_state.selected_option = None
    st.session_state.quiz_overall_start = None


def _start_quiz(category, difficulty, num_questions):
    questions = db.get_questions(category, difficulty, num_questions)
    if questions.empty:
        st.error(
            "😕 No questions are available yet for this Category/Difficulty. "
            "Please ask an admin to add some, or try a different combination."
        )
        return
    st.session_state.quiz_questions = questions.to_dict("records")
    st.session_state.quiz_category = category
    st.session_state.quiz_difficulty = difficulty
    st.session_state.quiz_num_questions = len(st.session_state.quiz_questions)
    st.session_state.quiz_index = 0
    st.session_state.quiz_correct = 0
    st.session_state.quiz_wrong = 0
    st.session_state.quiz_answers = []
    st.session_state.answered_current = False
    st.session_state.selected_option = None
    st.session_state.quiz_overall_start = time.time()
    st.session_state.quiz_stage = "active"
    timer.start_question_timer(st.session_state)
    st.rerun()


def _record_answer(selected_letter):
    """Lock in the answer for the current question (selected_letter may be
    None if the timer ran out with nothing selected)."""
    if st.session_state.answered_current:
        return
    q = st.session_state.quiz_questions[st.session_state.quiz_index]
    is_correct = selected_letter is not None and selected_letter == q["Correct_Answer"]
    if is_correct:
        st.session_state.quiz_correct += 1
    else:
        st.session_state.quiz_wrong += 1

    st.session_state.quiz_answers.append({
        "question": q["Question_Text"],
        "selected": selected_letter,
        "correct_answer": q["Correct_Answer"],
        "is_correct": is_correct,
        "explanation": q.get("Explanation", ""),
    })
    st.session_state.answered_current = True
    st.session_state.selected_option = selected_letter


def _go_next_question():
    st.session_state.quiz_index += 1
    st.session_state.answered_current = False
    st.session_state.selected_option = None
    if st.session_state.quiz_index >= len(st.session_state.quiz_questions):
        _finish_quiz()
    else:
        timer.start_question_timer(st.session_state)
    st.rerun()


def _finish_quiz():
    total_time = round(time.time() - st.session_state.quiz_overall_start, 1)
    total = len(st.session_state.quiz_questions)
    correct = st.session_state.quiz_correct
    percentage = scoring.calculate_percentage(correct, total)
    points_each = scoring.points_for_difficulty(st.session_state.quiz_difficulty)
    score = correct * points_each

    db.add_result(
        username=st.session_state.username,
        category=st.session_state.quiz_category,
        difficulty=st.session_state.quiz_difficulty,
        num_questions=total,
        score=score,
        percentage=percentage,
        time_taken=total_time,
    )

    st.session_state.quiz_final_time = total_time
    st.session_state.quiz_final_score = score
    st.session_state.quiz_final_percentage = percentage
    st.session_state.quiz_stage = "results"


# --------------------------------------------------------------------------
# UI: Setup screen
# --------------------------------------------------------------------------
def _render_setup():
    st.markdown("## 🎯 Start a New Quiz")
    st.write("Choose your category, difficulty, and how many questions you'd like to tackle.")

    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox("📚 Category", db.CATEGORIES)
    with col2:
        difficulty = st.selectbox("⚡ Difficulty", db.DIFFICULTIES)

    st.markdown("**🔢 Number of Questions**")
    preset = st.radio(
        "Quick select", ["5", "10", "20", "Custom"], horizontal=True, label_visibility="collapsed",
    )
    if preset == "Custom":
        num_questions = st.number_input(
            "Custom number of questions", min_value=1, max_value=50, value=15, step=1,
        )
    else:
        num_questions = int(preset)

    st.info(f"⏱️ Each question has a **{timer.QUESTION_SECONDS}-second** timer. Good luck!")

    if st.button("🚀 Start Quiz", use_container_width=True, type="primary"):
        _start_quiz(category, difficulty, int(num_questions))


# --------------------------------------------------------------------------
# UI: Active quiz screen
# --------------------------------------------------------------------------
@st.fragment(run_every=1)
def _timer_fragment():
    """Ticks once per second. Auto-submits a blank answer and advances
    when the 20-second countdown reaches zero."""
    if st.session_state.quiz_stage != "active":
        return
    remaining = timer.seconds_remaining(st.session_state)
    col1, col2 = st.columns([3, 1])
    with col1:
        st.progress(remaining / timer.QUESTION_SECONDS if timer.QUESTION_SECONDS else 0)
    with col2:
        emoji = "⏱️" if remaining > 5 else "🚨"
        st.metric(f"{emoji} Time Left", f"{remaining}s")

    if remaining <= 0 and not st.session_state.answered_current:
        _record_answer(None)
        st.rerun()


def _render_active():
    q_index = st.session_state.quiz_index
    questions = st.session_state.quiz_questions
    total = len(questions)
    q = questions[q_index]

    st.markdown(f"### Question {q_index + 1} of {total}")
    st.caption(f"📚 {st.session_state.quiz_category} • ⚡ {st.session_state.quiz_difficulty}")
    st.progress((q_index) / total)

    _timer_fragment()

    st.markdown(f"#### {q['Question_Text']}")

    options = {
        "A": q["Option_A"], "B": q["Option_B"],
        "C": q["Option_C"], "D": q["Option_D"],
    }

    if not st.session_state.answered_current:
        cols = st.columns(2)
        for i, (letter, text) in enumerate(options.items()):
            with cols[i % 2]:
                if st.button(f"{letter}. {text}", key=f"opt_{q_index}_{letter}", use_container_width=True):
                    _record_answer(letter)
                    st.rerun()
    else:
        # Show answered state with correctness feedback.
        last = st.session_state.quiz_answers[-1]
        for letter, text in options.items():
            if letter == last["correct_answer"]:
                st.success(f"✅ {letter}. {text}  (Correct Answer)")
            elif letter == last["selected"]:
                st.error(f"❌ {letter}. {text}  (Your Answer)")
            else:
                st.write(f"◻️ {letter}. {text}")

        if last["selected"] is None:
            st.warning("⏰ Time's up! No answer was selected for this question.")

        if last["explanation"]:
            st.info(f"💡 **Explanation:** {last['explanation']}")

        button_label = "➡️ Next Question" if q_index + 1 < total else "🏁 Finish Quiz"
        if st.button(button_label, use_container_width=True, type="primary"):
            _go_next_question()


# --------------------------------------------------------------------------
# UI: Results screen
# --------------------------------------------------------------------------
def _render_results():
    total = st.session_state.quiz_num_questions
    correct = st.session_state.quiz_correct
    wrong = st.session_state.quiz_wrong
    percentage = st.session_state.quiz_final_percentage
    score = st.session_state.quiz_final_score
    time_taken = st.session_state.quiz_final_time
    message, emoji = scoring.performance_message(percentage)

    st.markdown("## 🏁 Quiz Results")
    st.markdown(f"# {emoji} {message}")

    col1, col2, col3 = st.columns(3)
    col1.metric("✅ Correct", correct)
    col2.metric("❌ Wrong", wrong)
    col3.metric("📊 Percentage", f"{percentage}%")

    col4, col5, col6 = st.columns(3)
    col4.metric("🎯 Total Questions", total)
    col5.metric("🏆 Final Score", score)
    col6.metric("⏱️ Time Used", f"{time_taken}s")

    st.divider()
    with st.expander("📋 Review Your Answers"):
        for i, ans in enumerate(st.session_state.quiz_answers, start=1):
            icon = "✅" if ans["is_correct"] else "❌"
            st.markdown(f"**{icon} Q{i}: {ans['question']}**")
            st.caption(
                f"Your answer: {ans['selected'] or 'No answer'} • "
                f"Correct answer: {ans['correct_answer']}"
            )
            if ans["explanation"]:
                st.caption(f"💡 {ans['explanation']}")
            st.write("")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔁 Take Another Quiz", use_container_width=True, type="primary"):
            _reset_quiz_state()
            st.rerun()
    with col2:
        if st.button("📈 View My Performance", use_container_width=True):
            _reset_quiz_state()
            st.session_state.current_page = "My Performance"
            st.rerun()


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------
def render():
    if "quiz_stage" not in st.session_state:
        _reset_quiz_state()

    if st.session_state.quiz_stage == "setup":
        _render_setup()
    elif st.session_state.quiz_stage == "active":
        _render_active()
    elif st.session_state.quiz_stage == "results":
        _render_results()
