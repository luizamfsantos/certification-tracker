from __future__ import annotations

import textwrap
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from app.config import load_config
from app.models.enums import ModuleStatus
from app.services.metrics_service import (
    ALL_OPTION,
    get_date_bounds,
    get_filter_options,
    get_time_metrics,
)
from app.services.progress_service import get_progress_metrics


STATUS_COLORS = {
    ModuleStatus.NOT_SEEN.value: "#9CA3AF",
    ModuleStatus.SEEN.value: "#FACC15",
    ModuleStatus.MASTERED.value: "#22C55E",
}


def _minutes_to_hours(minutes: int) -> str:
    return f"{minutes / 60:.1f} h"


def _weekly_chart_df(weekly_df: pd.DataFrame) -> pd.DataFrame:
    chart_df = weekly_df.copy()
    chart_df["week_label"] = pd.to_datetime(chart_df["week_start"]).dt.strftime("%Y-%m-%d")
    return chart_df


def _progress_bar_chart_df(progress_bar_df: pd.DataFrame) -> pd.DataFrame:
    chart_df = progress_bar_df.copy()
    chart_df["label_wrapped"] = chart_df["label"].apply(
        lambda value: "<br>".join(textwrap.wrap(str(value), width=28))
    )
    return chart_df.sort_values("completion_pct", ascending=True)


def render() -> None:
    config = load_config()
    st.set_page_config(page_title="Dashboard", layout="wide")
    st.title("Certification Progress Dashboard")

    users_df, tracks_df = get_filter_options(config.data_dir)
    min_date, max_date = get_date_bounds(config.data_dir)

    with st.sidebar:
        st.header("Filters")
        date_range = st.date_input(
            "Date range",
            (min_date - timedelta(days=14), max_date),
            min_value=min_date - timedelta(days=365),
            max_value=max_date,
        )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date = date_range[0]
            end_date = date_range[1]
        else:
            single_date = (
                date_range[0]
                if isinstance(date_range, tuple) and len(date_range) == 1
                else date_range
            )
            start_date = single_date if isinstance(single_date, date) else max_date
            end_date = start_date

        user_options = [ALL_OPTION] + users_df["user_id"].tolist()
        user_filter = st.selectbox(
            "User", user_options, format_func=lambda v: _user_label(v, users_df)
        )

        track_options = [ALL_OPTION] + tracks_df["track_id"].tolist()
        track_filter = st.selectbox(
            "Track", track_options, format_func=lambda v: _track_label(v, tracks_df)
        )

    time_metrics = get_time_metrics(
        config.data_dir, start_date, end_date, user_filter, track_filter
    )
    progress_metrics = get_progress_metrics(config.data_dir, user_filter, track_filter)

    st.subheader("Time Tracking")
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Total", _minutes_to_hours(time_metrics.total_minutes))
    metric_col2.metric("Daily", _minutes_to_hours(time_metrics.daily_minutes))
    metric_col3.metric("Weekly", _minutes_to_hours(time_metrics.weekly_minutes))

    if not time_metrics.weekly_df.empty:
        weekly_chart_df = _weekly_chart_df(time_metrics.weekly_df)
        weekly_fig = px.bar(
            weekly_chart_df,
            x="week_label",
            y="minutes",
            title="Weekly Study Minutes",
            labels={"week_label": "Week Start", "minutes": "Minutes"},
            category_orders={"week_label": weekly_chart_df["week_label"].tolist()},
        )
        st.plotly_chart(weekly_fig, width="stretch")
    else:
        st.info("No time entries found for selected filters.")

    st.write("Breakdowns")
    breakdown_col1, breakdown_col2, breakdown_col3 = st.columns(3)
    breakdown_col1.dataframe(time_metrics.per_user_df, width="stretch")
    breakdown_col2.dataframe(time_metrics.per_module_df, width="stretch")
    breakdown_col3.dataframe(time_metrics.per_track_df, width="stretch")

    st.subheader("Progress Toward Certification")
    st.metric("Completion", f"{progress_metrics.completion_pct:.2f}%")

    pie_col, bar_col = st.columns(2)
    pie_fig = px.pie(
        progress_metrics.status_distribution_df,
        values="count",
        names="status",
        title="Status Distribution",
        color="status",
        color_discrete_map=STATUS_COLORS,
    )
    pie_col.plotly_chart(pie_fig, width="stretch")

    if not progress_metrics.progress_bar_df.empty:
        progress_chart_df = _progress_bar_chart_df(progress_metrics.progress_bar_df)
        bar_fig = px.bar(
            progress_chart_df,
            x="completion_pct",
            y="label_wrapped",
            orientation="h",
            title="Completion by Dimension",
            labels={"completion_pct": "Completion %", "label_wrapped": "Dimension"},
            height=120 + len(progress_chart_df) * 70,
        )
        bar_fig.update_layout(
            margin=dict(l=260, r=40, t=60, b=40),
            yaxis_title="Dimension",
            xaxis_title="Completion %",
        )
        bar_col.plotly_chart(bar_fig, width="stretch")
    else:
        bar_col.info("No progress data for selected filters.")


def _user_label(user_id: str, users_df: pd.DataFrame) -> str:
    if user_id == ALL_OPTION:
        return "All users"
    matched = users_df.loc[users_df["user_id"] == user_id, "display_name"]
    return matched.iloc[0] if not matched.empty else user_id


def _track_label(track_id: str, tracks_df: pd.DataFrame) -> str:
    if track_id == ALL_OPTION:
        return "All tracks"
    matched = tracks_df.loc[tracks_df["track_id"] == track_id, "track_name"]
    return matched.iloc[0] if not matched.empty else track_id


if __name__ == "__main__":
    render()
