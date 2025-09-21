# app/dashboard.py
import streamlit as st
import pandas as pd
import plotly as px
from core.progress import load_progress

def dashboard(username):
    st.header("📊 Your Progress Dashboard")

    data = load_progress(username)
    if not data:
        st.info("No progress yet. Try solving some exercises first!")
        return

    df = pd.DataFrame(data)

    # ✅ Success Rate
    df["success_rate"] = df["passed"] / df["total"] * 100
    overall_rate = df["success_rate"].mean()
    st.subheader("Overall Success Rate")
    st.progress(int(overall_rate))
    st.write(f"Average success rate: **{overall_rate:.2f}%**")

    # 📊 Per-task performance
    st.subheader("Performance by Task")
    fig1 = px.bar(df, x="task_id", y="success_rate", color="difficulty",
                  title="Average Success per Task")
    st.plotly_chart(fig1, use_container_width=True)

    # ⏱ Time spent trend
    st.subheader("Time Spent on Tasks")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    fig2 = px.line(df, x="timestamp", y="duration_seconds", color="task_id",
                   title="Time Spent per Attempt")
    st.plotly_chart(fig2, use_container_width=True)

    # 🥧 Difficulty breakdown
    st.subheader("Solved Tasks by Difficulty")
    fig3 = px.pie(df, names="difficulty", title="Difficulty Distribution")
    st.plotly_chart(fig3, use_container_width=True)

    # 📋 Recent attempts
    st.subheader("Recent Attempts")
    st.dataframe(df[["timestamp", "task_id", "passed", "total", "duration_seconds", "difficulty"]].tail(10))