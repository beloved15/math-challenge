"""
analytics.py
------------
Builds Plotly figures for the admin performance-analytics dashboard.
Each function takes the raw DataFrames from database_manager and returns
a ready-to-render Plotly figure (or None if there isn't enough data yet).
"""

import pandas as pd
import plotly.express as px


def quizzes_by_category_bar(results_df: pd.DataFrame):
    if results_df.empty:
        return None
    counts = results_df["Category"].value_counts().reset_index()
    counts.columns = ["Category", "Quizzes_Taken"]
    fig = px.bar(
        counts, x="Category", y="Quizzes_Taken", color="Category",
        title="Quizzes Taken per Category", text="Quizzes_Taken",
    )
    fig.update_layout(showlegend=False)
    return fig


def category_popularity_pie(results_df: pd.DataFrame):
    if results_df.empty:
        return None
    counts = results_df["Category"].value_counts().reset_index()
    counts.columns = ["Category", "Quizzes_Taken"]
    fig = px.pie(
        counts, names="Category", values="Quizzes_Taken",
        title="Category Popularity Share", hole=0.4,
    )
    return fig


def average_score_by_category_bar(results_df: pd.DataFrame):
    if results_df.empty:
        return None
    avg = results_df.groupby("Category")["Percentage"].mean().reset_index()
    avg["Percentage"] = avg["Percentage"].round(1)
    avg = avg.sort_values("Percentage")
    fig = px.bar(
        avg, x="Percentage", y="Category", orientation="h", color="Percentage",
        title="Average Score % by Category (lowest = most difficult)",
        color_continuous_scale="RdYlGn",
    )
    return fig


def average_score_by_difficulty_bar(results_df: pd.DataFrame):
    if results_df.empty:
        return None
    avg = results_df.groupby("Difficulty_Level")["Percentage"].mean().reset_index()
    avg["Percentage"] = avg["Percentage"].round(1)
    order = ["Easy", "Intermediate", "Advanced"]
    avg["Difficulty_Level"] = pd.Categorical(avg["Difficulty_Level"], categories=order, ordered=True)
    avg = avg.sort_values("Difficulty_Level")
    fig = px.bar(
        avg, x="Difficulty_Level", y="Percentage", color="Difficulty_Level",
        title="Average Score % by Difficulty",
    )
    return fig


def performance_trend_line(results_df: pd.DataFrame):
    """Average daily percentage score trend across all users."""
    if results_df.empty:
        return None
    df = results_df.copy()
    df["Date_Played"] = pd.to_datetime(df["Date_Played"], errors="coerce")
    df = df.dropna(subset=["Date_Played"])
    if df.empty:
        return None
    df["Day"] = df["Date_Played"].dt.date
    trend = df.groupby("Day")["Percentage"].mean().reset_index()
    trend["Percentage"] = trend["Percentage"].round(1)
    fig = px.line(
        trend, x="Day", y="Percentage", markers=True,
        title="Average Score Trend Over Time",
    )
    return fig


def most_popular_category(results_df: pd.DataFrame):
    if results_df.empty:
        return "N/A"
    return results_df["Category"].value_counts().idxmax()


def most_difficult_category(results_df: pd.DataFrame):
    if results_df.empty:
        return "N/A"
    avg = results_df.groupby("Category")["Percentage"].mean()
    return avg.idxmin()
