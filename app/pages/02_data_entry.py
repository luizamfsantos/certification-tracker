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
    time_user_id = st.selectbox(
        "User",
        users,
        index=None,
        placeholder="Select a user",
        format_func=lambda x: _display_name(x, users_df),
        key="time_user_select",
    )
    time_track_id = st.selectbox(
        "Track",
        tracks,
        index=None,
        placeholder="Select a track",
        format_func=lambda x: _track_name(x, tracks_df),
        key="time_track_select",
    )
    modules_df = (
        get_modules_for_track(config.data_dir, time_track_id) if time_track_id else pd.DataFrame()
    )
    time_module_options = modules_df["module_id"].tolist() if not modules_df.empty else []
    time_module_id = st.selectbox(
        "Module (optional)",
        time_module_options,
        index=None,
        placeholder="Select a module" if time_track_id else "Select a track first",
        disabled=time_track_id is None,
        format_func=lambda x: _module_name(x, modules_df),
        key="time_module_select",
    )
    minutes_spent = st.number_input("Minutes spent", min_value=1, max_value=600, value=30, step=5)
    entry_date = st.date_input("Entry date", value=date.today())
    submit_time = st.button(
        "Add time entry",
        disabled=(time_user_id is None or time_track_id is None),
        key="time_entry_button",
    )
    if submit_time:
        try:
            payload = TimeEntryInput(
                user_id=time_user_id or "",
                track_id=time_track_id or "",
                module_id=time_module_id or None,
                minutes_spent=int(minutes_spent),
                entry_date=entry_date,
            )
            append_time_entry(config.data_dir, payload)
            st.success("Time entry added.")
        except ValueError as exc:
            st.error(str(exc))

    st.subheader("Module Progress Update")
    progress_user_id = st.selectbox(
        "User",
        users,
        index=None,
        placeholder="Select a user",
        format_func=lambda x: _display_name(x, users_df),
        key="progress_user_select",
    )
    progress_track_id = st.selectbox(
        "Track",
        tracks,
        index=None,
        placeholder="Select a track",
        format_func=lambda x: _track_name(x, tracks_df),
        key="progress_track_select",
    )
    progress_modules_df = (
        get_modules_for_track(config.data_dir, progress_track_id)
        if progress_track_id
        else pd.DataFrame()
    )
    progress_module_options = (
        progress_modules_df["module_id"].tolist() if not progress_modules_df.empty else []
    )
    progress_module_id = st.selectbox(
        "Module",
        progress_module_options,
        index=None,
        placeholder="Select a module" if progress_track_id else "Select a track first",
        disabled=progress_track_id is None,
        format_func=lambda x: _module_name(x, progress_modules_df),
        key="progress_module_select",
    )
    status_values = [item.value for item in ModuleStatus]
    status_value = st.selectbox(
        "Status",
        status_values,
        index=None,
        placeholder="Select a status",
        key="progress_status_select",
    )
    submit_progress = st.button(
        "Add progress update",
        disabled=(
            progress_user_id is None
            or progress_track_id is None
            or progress_module_id is None
            or status_value is None
        ),
        key="progress_entry_button",
    )
    if submit_progress:
        try:
            progress_payload = ModuleProgressInput(
                user_id=progress_user_id or "",
                module_id=progress_module_id or "",
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
