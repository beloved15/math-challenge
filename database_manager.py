"""
database_manager.py
--------------------
Central data-access layer for the Mathematics Quiz Challenge App.

All reads/writes to the Excel "database" go through this module so that
the rest of the application never touches openpyxl/pandas file paths
directly. This keeps the I/O logic in one place and makes it easy to
swap the storage backend later (e.g. to a real SQL database) without
touching page/UI code.
"""

import os
import threading
import pandas as pd
from datetime import datetime

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "database")

USERS_FILE = os.path.join(DB_DIR, "users.xlsx")
QUESTIONS_FILE = os.path.join(DB_DIR, "questions.xlsx")
RESULTS_FILE = os.path.join(DB_DIR, "results.xlsx")
LEADERBOARD_FILE = os.path.join(DB_DIR, "leaderboard.xlsx")

# --------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------
USERS_COLUMNS = [
    "User_ID", "Username", "Full_Name", "Email", "Phone_Number", "Password",
    "Registration_Date", "Total_Games_Played", "Total_Score",
    "Average_Percentage", "Current_Level",
]

QUESTIONS_COLUMNS = [
    "Question_ID", "Category", "Difficulty_Level", "Question_Text",
    "Option_A", "Option_B", "Option_C", "Option_D", "Correct_Answer",
    "Explanation",
]

RESULTS_COLUMNS = [
    "Result_ID", "Username", "Category", "Difficulty_Level",
    "Number_of_Questions", "Score", "Percentage", "Time_Taken", "Date_Played",
]

LEADERBOARD_COLUMNS = [
    "Username", "Weekly_Score", "Games_Played", "Average_Percentage", "Rank",
]

CATEGORIES = [
    "Addition", "Subtraction", "Multiplication", "Division",
    "Algebra", "Statistics", "Mixture",
]
DIFFICULTIES = ["Easy", "Intermediate", "Advanced"]


# In-process locks (one per file) guarding concurrent writes. Streamlit
# serves multiple user sessions from the same process via threads, so this
# prevents two sessions from writing the same workbook at the same instant
# and corrupting it. (Not a substitute for a real DB under heavy multi-
# process load, but sufficient for a single-server Streamlit deployment.)
_FILE_LOCKS = {}
_LOCKS_GUARD = threading.Lock()


def _lock_path(file_path: str) -> threading.Lock:
    with _LOCKS_GUARD:
        if file_path not in _FILE_LOCKS:
            _FILE_LOCKS[file_path] = threading.Lock()
        return _FILE_LOCKS[file_path]


def ensure_database_exists() -> None:
    """Create the database folder and all required Excel files (with the
    correct headers) if they do not already exist. Safe to call on every
    app startup."""
    os.makedirs(DB_DIR, exist_ok=True)

    if not os.path.exists(USERS_FILE):
        pd.DataFrame(columns=USERS_COLUMNS).to_excel(USERS_FILE, index=False)

    if not os.path.exists(QUESTIONS_FILE):
        df = pd.DataFrame(columns=QUESTIONS_COLUMNS)
        df.to_excel(QUESTIONS_FILE, index=False)

    if not os.path.exists(RESULTS_FILE):
        pd.DataFrame(columns=RESULTS_COLUMNS).to_excel(RESULTS_FILE, index=False)

    if not os.path.exists(LEADERBOARD_FILE):
        pd.DataFrame(columns=LEADERBOARD_COLUMNS).to_excel(LEADERBOARD_FILE, index=False)


# --------------------------------------------------------------------------
# Generic helpers
# --------------------------------------------------------------------------
def read_table(file_path: str, columns: list) -> pd.DataFrame:
    """Read an Excel table safely, returning an empty (but correctly
    columned) DataFrame if the file is missing or corrupted."""
    try:
        df = pd.read_excel(file_path, engine="openpyxl")
        # Guarantee every expected column exists even on legacy files.
        for col in columns:
            if col not in df.columns:
                df[col] = None
        return df[columns]
    except (FileNotFoundError, ValueError):
        return pd.DataFrame(columns=columns)


def write_table(file_path: str, df: pd.DataFrame) -> None:
    """Persist a DataFrame back to Excel, guarded by a file lock so two
    Streamlit sessions writing at once don't corrupt the workbook."""
    with _lock_path(file_path):
        df.to_excel(file_path, index=False)


def next_id(df: pd.DataFrame, id_column: str) -> int:
    """Return the next auto-increment integer ID for a table."""
    if df.empty or df[id_column].isna().all():
        return 1
    return int(pd.to_numeric(df[id_column], errors="coerce").fillna(0).max()) + 1


def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# --------------------------------------------------------------------------
# Users
# --------------------------------------------------------------------------
def load_users() -> pd.DataFrame:
    return read_table(USERS_FILE, USERS_COLUMNS)


def save_users(df: pd.DataFrame) -> None:
    write_table(USERS_FILE, df)


def get_user(username: str):
    df = load_users()
    match = df[df["Username"].astype(str).str.lower() == str(username).lower()]
    return match.iloc[0] if not match.empty else None


def username_exists(username: str) -> bool:
    return get_user(username) is not None


def email_exists(email: str) -> bool:
    df = load_users()
    return bool((df["Email"].astype(str).str.lower() == str(email).lower()).any())


def create_user(username, full_name, email, phone, hashed_password) -> None:
    df = load_users()
    new_row = {
        "User_ID": next_id(df, "User_ID"),
        "Username": username,
        "Full_Name": full_name,
        "Email": email,
        "Phone_Number": phone,
        "Password": hashed_password,
        "Registration_Date": timestamp(),
        "Total_Games_Played": 0,
        "Total_Score": 0,
        "Average_Percentage": 0.0,
        "Current_Level": "Beginner",
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_users(df)


def update_user_stats(username: str, score: int, percentage: float) -> None:
    """Update a user's aggregate stats after finishing a quiz."""
    df = load_users()
    idx = df.index[df["Username"].astype(str).str.lower() == username.lower()]
    if len(idx) == 0:
        return
    i = idx[0]
    games_played = int(df.at[i, "Total_Games_Played"] or 0) + 1
    total_score = float(df.at[i, "Total_Score"] or 0) + score
    prev_avg = float(df.at[i, "Average_Percentage"] or 0)
    # Running average of percentage scores across all games played.
    new_avg = ((prev_avg * (games_played - 1)) + percentage) / games_played

    if new_avg >= 90:
        level = "Master"
    elif new_avg >= 70:
        level = "Advanced"
    elif new_avg >= 50:
        level = "Intermediate"
    else:
        level = "Beginner"

    df.at[i, "Total_Games_Played"] = games_played
    df.at[i, "Total_Score"] = total_score
    df.at[i, "Average_Percentage"] = round(new_avg, 2)
    df.at[i, "Current_Level"] = level
    save_users(df)


# --------------------------------------------------------------------------
# Questions
# --------------------------------------------------------------------------
def load_questions() -> pd.DataFrame:
    return read_table(QUESTIONS_FILE, QUESTIONS_COLUMNS)


def save_questions(df: pd.DataFrame) -> None:
    write_table(QUESTIONS_FILE, df)


def get_questions(category: str, difficulty: str, n: int) -> pd.DataFrame:
    """Return up to n random questions for a category/difficulty.
    'Mixture' pulls from every real category."""
    df = load_questions()
    if category != "Mixture":
        df = df[df["Category"] == category]
    else:
        df = df[df["Category"] != "Mixture"]
    df = df[df["Difficulty_Level"] == difficulty]
    if df.empty:
        return df
    n = min(n, len(df))
    return df.sample(n=n).reset_index(drop=True)


def add_question(category, difficulty, text, a, b, c, d, correct, explanation) -> None:
    df = load_questions()
    new_row = {
        "Question_ID": next_id(df, "Question_ID"),
        "Category": category,
        "Difficulty_Level": difficulty,
        "Question_Text": text,
        "Option_A": a, "Option_B": b, "Option_C": c, "Option_D": d,
        "Correct_Answer": correct,
        "Explanation": explanation,
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_questions(df)


def update_question(question_id: int, updates: dict) -> None:
    df = load_questions()
    idx = df.index[df["Question_ID"] == question_id]
    if len(idx) == 0:
        return
    for k, v in updates.items():
        df.at[idx[0], k] = v
    save_questions(df)


def delete_question(question_id: int) -> None:
    df = load_questions()
    df = df[df["Question_ID"] != question_id]
    save_questions(df)


# --------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------
def load_results() -> pd.DataFrame:
    return read_table(RESULTS_FILE, RESULTS_COLUMNS)


def save_results(df: pd.DataFrame) -> None:
    write_table(RESULTS_FILE, df)


def add_result(username, category, difficulty, num_questions, score, percentage, time_taken) -> None:
    df = load_results()
    new_row = {
        "Result_ID": next_id(df, "Result_ID"),
        "Username": username,
        "Category": category,
        "Difficulty_Level": difficulty,
        "Number_of_Questions": num_questions,
        "Score": score,
        "Percentage": percentage,
        "Time_Taken": time_taken,
        "Date_Played": timestamp(),
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_results(df)
    update_user_stats(username, score, percentage)
    rebuild_leaderboard()


def get_user_results(username: str) -> pd.DataFrame:
    df = load_results()
    return df[df["Username"].astype(str).str.lower() == username.lower()]


# --------------------------------------------------------------------------
# Leaderboard
# --------------------------------------------------------------------------
def load_leaderboard() -> pd.DataFrame:
    return read_table(LEADERBOARD_FILE, LEADERBOARD_COLUMNS)


def save_leaderboard(df: pd.DataFrame) -> None:
    write_table(LEADERBOARD_FILE, df)


def rebuild_leaderboard(days: int = 7) -> pd.DataFrame:
    """Recompute the weekly leaderboard from results in the last `days` days."""
    results = load_results()
    if results.empty:
        save_leaderboard(pd.DataFrame(columns=LEADERBOARD_COLUMNS))
        return load_leaderboard()

    results["Date_Played"] = pd.to_datetime(results["Date_Played"], errors="coerce")
    cutoff = datetime.now() - pd.Timedelta(days=days)
    weekly = results[results["Date_Played"] >= cutoff]

    if weekly.empty:
        save_leaderboard(pd.DataFrame(columns=LEADERBOARD_COLUMNS))
        return load_leaderboard()

    grouped = weekly.groupby("Username").agg(
        Weekly_Score=("Score", "sum"),
        Games_Played=("Score", "count"),
        Average_Percentage=("Percentage", "mean"),
    ).reset_index()

    grouped["Average_Percentage"] = grouped["Average_Percentage"].round(2)
    grouped = grouped.sort_values("Weekly_Score", ascending=False).reset_index(drop=True)
    grouped["Rank"] = grouped.index + 1

    grouped = grouped[LEADERBOARD_COLUMNS]
    save_leaderboard(grouped)
    return grouped


def get_weekly_winner():
    lb = load_leaderboard()
    if lb.empty:
        return None
    return lb.sort_values("Rank").iloc[0]
