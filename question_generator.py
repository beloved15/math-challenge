"""
question_generator.py
----------------------
Generates a starter bank of math questions so the app is usable out of
the box. Runs once on first launch (when questions.xlsx is empty) and
writes the questions straight into the Excel database via
database_manager.add_question(). Admins can add/edit/delete further
questions afterwards from the Admin Dashboard.
"""

import random

from utils import database_manager as db

RANGES = {
    "Easy": (1, 10),
    "Intermediate": (10, 50),
    "Advanced": (50, 200),
}


def _distinct_wrong_options(correct, spread):
    """Generate 3 plausible-but-wrong numeric distractors.
    `spread` must be at least 2 -- a spread of -1..1 only yields 3 possible
    distinct values total and can never produce 4 unique options."""
    spread = max(2, spread)
    options = {correct}
    attempts = 0
    while len(options) < 4 and attempts < 100:
        delta = random.randint(-spread, spread)
        candidate = correct + delta if delta != 0 else correct + random.choice([-1, 1])
        options.add(candidate)
        attempts += 1
        if attempts % 20 == 0:
            spread += 2  # widen the net if we're struggling to find new values
    return list(options)


def _make_arithmetic_question(op: str, difficulty: str):
    lo, hi = RANGES[difficulty]
    a, b = random.randint(lo, hi), random.randint(lo, hi)

    if op == "Addition":
        correct, text = a + b, f"What is {a} + {b}?"
    elif op == "Subtraction":
        a, b = max(a, b), min(a, b)
        correct, text = a - b, f"What is {a} - {b}?"
    elif op == "Multiplication":
        mult_lo, mult_hi = min(lo, 12), min(max(hi, lo), 12)
        mult_lo = min(mult_lo, mult_hi)
        a, b = random.randint(mult_lo, mult_hi), random.randint(mult_lo, mult_hi)
        correct, text = a * b, f"What is {a} × {b}?"
    else:  # Division - construct so it divides evenly
        div_lo, div_hi = min(lo, 12), min(max(hi, lo), 12)
        div_lo = min(div_lo, div_hi)
        b = random.randint(max(1, div_lo), div_hi)
        a = b * random.randint(div_lo, div_hi)
        correct, text = a // b, f"What is {a} ÷ {b}?"

    spread = max(2, int(abs(correct) * 0.2) + 1)
    options = _distinct_wrong_options(correct, spread)
    random.shuffle(options)
    letters = ["A", "B", "C", "D"]
    correct_letter = letters[options.index(correct)]
    explanation = f"{text} = {correct}"
    return text, options, correct_letter, explanation


def _make_algebra_question(difficulty: str):
    lo, hi = RANGES[difficulty]
    x = random.randint(1, min(hi, 20))
    a = random.randint(1, 10)
    b = random.randint(1, hi)
    result = a * x + b
    text = f"Solve for x: {a}x + {b} = {result}"
    correct = x
    options = _distinct_wrong_options(correct, max(2, x // 3 + 1))
    random.shuffle(options)
    letters = ["A", "B", "C", "D"]
    correct_letter = letters[options.index(correct)]
    explanation = f"{a}x = {result} - {b} = {result - b}, so x = {correct}"
    return text, options, correct_letter, explanation


def _make_statistics_question(difficulty: str):
    lo, hi = RANGES[difficulty]
    size = {"Easy": 4, "Intermediate": 5, "Advanced": 6}[difficulty]
    nums = [random.randint(lo, hi) for _ in range(size)]
    kind = random.choice(["mean", "max", "min", "range"])

    if kind == "mean":
        correct = round(sum(nums) / len(nums), 1)
        text = f"What is the mean (average) of {nums}?"
        explanation = f"Sum = {sum(nums)}, divided by {len(nums)} = {correct}"
    elif kind == "max":
        correct = max(nums)
        text = f"What is the maximum value in {nums}?"
        explanation = f"The largest number in the list is {correct}"
    elif kind == "min":
        correct = min(nums)
        text = f"What is the minimum value in {nums}?"
        explanation = f"The smallest number in the list is {correct}"
    else:
        correct = max(nums) - min(nums)
        text = f"What is the range of {nums}?"
        explanation = f"Range = max - min = {max(nums)} - {min(nums)} = {correct}"

    spread = max(2, int(abs(correct) * 0.3) + 1)
    options = _distinct_wrong_options(correct, spread)
    random.shuffle(options)
    letters = ["A", "B", "C", "D"]
    correct_letter = letters[options.index(correct)]
    return text, options, correct_letter, explanation


def generate_question(category: str, difficulty: str):
    if category in ("Addition", "Subtraction", "Multiplication", "Division"):
        return _make_arithmetic_question(category, difficulty)
    elif category == "Algebra":
        return _make_algebra_question(difficulty)
    elif category == "Statistics":
        return _make_statistics_question(difficulty)
    else:
        return _make_arithmetic_question("Addition", difficulty)


def seed_sample_questions(per_bucket: int = 15) -> None:
    """Populate questions.xlsx with a starter bank if it's empty.
    Creates `per_bucket` questions for every (category, difficulty) pair."""
    existing = db.load_questions()
    if not existing.empty:
        return  # Already seeded / admin has real content - don't overwrite.

    categories = ["Addition", "Subtraction", "Multiplication", "Division", "Algebra", "Statistics"]
    rows = []
    next_id = 1
    for category in categories:
        for difficulty in db.DIFFICULTIES:
            for _ in range(per_bucket):
                text, options, correct_letter, explanation = generate_question(category, difficulty)
                rows.append({
                    "Question_ID": next_id,
                    "Category": category,
                    "Difficulty_Level": difficulty,
                    "Question_Text": text,
                    "Option_A": options[0], "Option_B": options[1],
                    "Option_C": options[2], "Option_D": options[3],
                    "Correct_Answer": correct_letter,
                    "Explanation": explanation,
                })
                next_id += 1
    import pandas as pd
    df = pd.DataFrame(rows, columns=db.QUESTIONS_COLUMNS)
    db.save_questions(df)
