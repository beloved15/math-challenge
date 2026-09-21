"""
scoring.py
----------
Pure functions for computing quiz scores and performance messages.
No Streamlit or I/O dependencies -> easy to unit test.
"""


def calculate_percentage(correct: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((correct / total) * 100, 2)


def performance_message(percentage: float) -> tuple:
    """Return (message, emoji) for a given percentage score."""
    if percentage >= 90:
        return "Excellent! 🏆", "🏆"
    elif percentage >= 70:
        return "Very Good! 🌟", "🌟"
    elif percentage >= 50:
        return "Good! 👍", "👍"
    else:
        return "Needs Improvement 💪", "💪"


def points_for_difficulty(difficulty: str) -> int:
    """Base points awarded per correct answer, scaled by difficulty."""
    return {"Easy": 1, "Intermediate": 2, "Advanced": 3}.get(difficulty, 1)
