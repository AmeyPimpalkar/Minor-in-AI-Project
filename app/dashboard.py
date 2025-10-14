# app/dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
from core.progress import load_progress
import os
import json


def load_user_progress(username):
    """Load per-user error trends from the learning log."""
    if not os.path.exists("data/user_learning_log.json"):
        return pd.DataFrame()
    with open("data/user_learning_log.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    user_data = data.get(username, {})
    if not user_data:
        return pd.DataFrame()
    return pd.DataFrame(list(user_data.items()), columns=["Error Type", "Count"])


def dashboard(username):
    st.header("📊 Your Progress Dashboard")

    # --- Overall coding progress ---
    data = load_progress(username)
    if not data:
        st.info("No progress yet. Try solving some exercises first!")
    else:
        df = pd.DataFrame(data)
        df["success_rate"] = df.apply(
            lambda row: (row["passed"] / row["total"]) * 100 if row["total"] > 0 else 0,
            axis=1,
        )

        overall_rate = df["success_rate"].mean()
        if pd.isna(overall_rate) or overall_rate == float("inf"):
            overall_rate = 0

        st.subheader("🏆 Overall Success Rate")
        st.progress(int(overall_rate))
        st.write(f"Average success rate: **{overall_rate:.2f}%**")

        # --- Performance by Task ---
        st.subheader("📘 Performance by Task")
        fig1 = px.bar(
            df,
            x="task_id",
            y="success_rate",
            color="difficulty",
            title="Average Success per Task",
        )
        st.plotly_chart(fig1, use_container_width=True)

        # --- Time Spent Trend ---
        st.subheader("⏱️ Time Spent on Tasks")
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        fig2 = px.line(
            df,
            x="timestamp",
            y="duration_seconds",
            color="task_id",
            title="Time Spent per Attempt",
        )
        st.plotly_chart(fig2, use_container_width=True)

        # --- Difficulty Distribution ---
        st.subheader("🎯 Solved Tasks by Difficulty")
        fig3 = px.pie(df, names="difficulty", title="Difficulty Distribution")
        st.plotly_chart(fig3, use_container_width=True)

        # --- Recent Attempts Table ---
        st.subheader("🧾 Recent Attempts")
        st.dataframe(
            df[["timestamp", "task_id", "passed", "total", "duration_seconds", "difficulty"]].tail(10)
        )

    # --- New Section: Error Trends from user_learning_log.json ---
    df_error = load_user_progress(username)
    if not df_error.empty:
        st.subheader("🧠 Error Trends (Learning Insights)")
        fig = px.bar(
            df_error,
            x="Error Type",
            y="Count",
            color="Error Type",
            title="Error Frequency per Type",
        )
        st.plotly_chart(fig, use_container_width=True)

        most_common_error = df_error.sort_values(by="Count", ascending=False).iloc[0]
        st.info(
            f"💡 You often encounter **{most_common_error['Error Type']}** errors. "
            f"Consider reviewing that concept for improvement!"
        )
    else:
        st.info("No error data recorded yet. Start coding to see insights!")