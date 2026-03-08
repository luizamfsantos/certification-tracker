from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from app.config import load_config
from app.models.enums import ModuleStatus
from app.models.schemas import ModuleProgressInput, TimeEntryInput
from app.services.ingestion_service import append_module_progress, append_time_entry
from app.services.metrics_service import get_filter_options, get_modules_for_track


def render() -> None:
    config = load_config()
    st.set_page_config(page_title="Data Entry", layout="wide")
    st.title("Data Entry")
    st.caption("Use forms below to append tracker data to committed CSV files.")

    users_df, tracks_df = get_filter_options(config.data_dir)
    users = users_df["user_id"].tolist()
    tracks = tracks_df["track_id"].tolist()

    st.subheader("Time Entry")
    with st.form("time_entry_form", clear_on_submit=True):
        time_user_id = st.selectbox("User", users, format_func=lambda x: _display_name(x, users_df))
        time_track_id = st.selectbox("Track", tracks, format_func=lambda x: _track_name(x, tracks_df))
        modules_df = get_modules_for_track(config.data_dir, time_track_id)
        module_options = [""] + modules_df["module_id"].tolist()
        time_module_id = st.selectbox(
            "Module (optional)",
            module_options,
            format_func=lambda x: _module_name(x, modules_df) if x else "-- none --",
        )
        minutes_spent = st.number_input("Minutes spent", min_value=1, max_value=600, value=30, step=5)
        entry_date = st.date_input("Entry date", value=date.today())
        submit_time = st.form_submit_button("Add time entry")
        if submit_time:
            try:
                payload = TimeEntryInput(
                    user_id=time_user_id,
                    track_id=time_track_id,
                    module_id=time_module_id or None,
                    minutes_spent=int(minutes_spent),
                    entry_date=entry_date,
                )
                append_time_entry(config.data_dir, payload)
                st.success("Time entry added.")
            except ValueError as exc:
                st.error(str(exc))

    st.subheader("Module Progress Update")
    with st.form("progress_form", clear_on_submit=True):
        progress_user_id = st.selectbox("User", users, format_func=lambda x: _display_name(x, users_df))
        progress_track_id = st.selectbox("Track", tracks, format_func=lambda x: _track_name(x, tracks_df))
        progress_modules_df = get_modules_for_track(config.data_dir, progress_track_id)
        progress_module_id = st.selectbox(
            "Module",
            progress_modules_df["module_id"].tolist(),
            format_func=lambda x: _module_name(x, progress_modules_df),
        )
        status_value = st.selectbox("Status", [item.value for item in ModuleStatus])
        submit_progress = st.form_submit_button("Add progress update")
        if submit_progress:
            try:
                progress_payload = ModuleProgressInput(
                    user_id=progress_user_id,
                    module_id=progress_module_id,
                    status=ModuleStatus(status_value),
                )
                append_module_progress(config.data_dir, progress_payload)
                st.success("Progress update added.")
            except ValueError as exc:
                st.error(str(exc))


def _display_name(user_id: str, users_df: pd.DataFrame) -> str:
    match = users_df.loc[users_df["user_id"] == user_id, "display_name"]
    return match.iloc[0] if not match.empty else user_id


def _track_name(track_id: str, tracks_df: pd.DataFrame) -> str:
    match = tracks_df.loc[tracks_df["track_id"] == track_id, "track_name"]
    return match.iloc[0] if not match.empty else track_id


def _module_name(module_id: str, modules_df: pd.DataFrame) -> str:
    match = modules_df.loc[modules_df["module_id"] == module_id, "module_name"]
    return match.iloc[0] if not match.empty else module_id


if __name__ == "__main__":
    render()
