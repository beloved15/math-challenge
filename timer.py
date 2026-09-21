"""
timer.py
--------
Helpers for the per-question 20-second countdown.

Streamlit re-runs the whole script on every interaction rather than
keeping a persistent background thread, so the timer is implemented as
a wall-clock timestamp stored in session_state. The quiz page wraps its
timer display in an `st.fragment(run_every=1)` fragment (see pages/quiz.py)
so the countdown visually ticks down once per second without rerunning
(and losing state on) the whole app.
"""

import time

QUESTION_SECONDS = 20


def start_question_timer(session_state) -> None:
    """Record the start time for the current question."""
    session_state.question_start_time = time.time()


def seconds_remaining(session_state) -> int:
    """Return whole seconds left before the current question expires."""
    start = session_state.get("question_start_time")
    if start is None:
        return QUESTION_SECONDS
    elapsed = time.time() - start
    remaining = QUESTION_SECONDS - int(elapsed)
    return max(0, remaining)


def is_time_up(session_state) -> bool:
    return seconds_remaining(session_state) <= 0


def elapsed_seconds(session_state) -> float:
    start = session_state.get("question_start_time")
    if start is None:
        return 0.0
    return round(time.time() - start, 1)
