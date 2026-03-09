from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from app.services.duckdb_service import query_df, query_scalar


ALL_OPTION = "ALL"


@dataclass(frozen=True)
class TimeMetricsResult:
    total_minutes: int
    daily_minutes: int
    weekly_minutes: int
    daily_df: pd.DataFrame
    weekly_df: pd.DataFrame
    per_user_df: pd.DataFrame
    per_module_df: pd.DataFrame
    per_track_df: pd.DataFrame


def get_date_bounds(data_dir: Path) -> tuple[date, date]:
    query = "SELECT MIN(CAST(entry_date AS DATE)), MAX(CAST(entry_date AS DATE)) FROM time_entries;"
    min_date, max_date = query_df(data_dir, query).iloc[0].tolist()
    if pd.isna(min_date) or pd.isna(max_date):
        today = date.today()
        return today, today
    return min_date, max_date


def get_filter_options(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    users_df = query_df(
        data_dir,
        "SELECT user_id, display_name FROM users ORDER BY display_name;",
    )
    tracks_df = query_df(
        data_dir,
        "SELECT track_id, track_name FROM certification_tracks ORDER BY track_name;",
    )
    return users_df, tracks_df


def get_modules_for_track(data_dir: Path, track_id: str | None = None) -> pd.DataFrame:
    query = (
        "SELECT module_id, module_name, track_id FROM modules "
        "WHERE (? IS NULL OR track_id = ?) ORDER BY module_order, module_name;"
    )
    return query_df(data_dir, query, [track_id, track_id])


def _build_time_filter_clause(
    start_date: date,
    end_date: date,
    user_id: str | None,
    track_id: str | None,
) -> tuple[str, list[object]]:
    clauses = ["CAST(t.entry_date AS DATE) BETWEEN ? AND ?"]
    params: list[object] = [start_date, end_date]
    if user_id and user_id != ALL_OPTION:
        clauses.append("t.user_id = ?")
        params.append(user_id)
    if track_id and track_id != ALL_OPTION:
        clauses.append("t.track_id = ?")
        params.append(track_id)
    return " AND ".join(clauses), params


def get_time_metrics(
    data_dir: Path,
    start_date: date,
    end_date: date,
    user_id: str | None,
    track_id: str | None,
) -> TimeMetricsResult:
    where_clause, base_params = _build_time_filter_clause(start_date, end_date, user_id, track_id)

    total_query = (
        f"SELECT COALESCE(SUM(t.minutes_spent), 0) FROM time_entries t WHERE {where_clause};"
    )
    total_minutes = _to_int(query_scalar(data_dir, total_query, base_params))

    daily_query = (
        f"SELECT COALESCE(SUM(t.minutes_spent), 0) FROM time_entries t "
        f"WHERE {where_clause} AND CAST(t.entry_date AS DATE) = ?;"
    )
    daily_minutes = _to_int(query_scalar(data_dir, daily_query, [*base_params, end_date]))

    weekly_query = (
        f"SELECT COALESCE(SUM(t.minutes_spent), 0) FROM time_entries t "
        f"WHERE {where_clause} "
        f"AND date_trunc('week', CAST(t.entry_date AS DATE)) = date_trunc('week', ?::DATE);"
    )
    weekly_minutes = _to_int(query_scalar(data_dir, weekly_query, [*base_params, end_date]))

    daily_df = query_df(
        data_dir,
        (
            "SELECT CAST(t.entry_date AS DATE) AS entry_date, "
            "SUM(t.minutes_spent) AS minutes "
            f"FROM time_entries t WHERE {where_clause} "
            "GROUP BY 1 ORDER BY 1;"
        ),
        base_params,
    )

    weekly_df = query_df(
        data_dir,
        (
            "SELECT CAST(date_trunc('week', CAST(t.entry_date AS DATE)) AS DATE) AS week_start, "
            "SUM(t.minutes_spent) AS minutes "
            f"FROM time_entries t WHERE {where_clause} "
            "GROUP BY 1 ORDER BY 1;"
        ),
        base_params,
    )

    per_user_df = query_df(
        data_dir,
        (
            "SELECT u.display_name AS user_name, SUM(t.minutes_spent) AS minutes "
            "FROM time_entries t "
            "JOIN users u ON u.user_id = t.user_id "
            f"WHERE {where_clause} "
            "GROUP BY 1 ORDER BY 2 DESC, 1;"
        ),
        base_params,
    )

    per_module_df = query_df(
        data_dir,
        (
            "SELECT m.module_name, SUM(t.minutes_spent) AS minutes "
            "FROM time_entries t "
            "LEFT JOIN modules m ON m.module_id = t.module_id "
            f"WHERE {where_clause} "
            "GROUP BY 1 ORDER BY 2 DESC, 1;"
        ),
        base_params,
    )

    per_track_df = query_df(
        data_dir,
        (
            "SELECT ct.track_name, SUM(t.minutes_spent) AS minutes "
            "FROM time_entries t "
            "JOIN certification_tracks ct ON ct.track_id = t.track_id "
            f"WHERE {where_clause} "
            "GROUP BY 1 ORDER BY 2 DESC, 1;"
        ),
        base_params,
    )

    return TimeMetricsResult(
        total_minutes=total_minutes,
        daily_minutes=daily_minutes,
        weekly_minutes=weekly_minutes,
        daily_df=daily_df,
        weekly_df=weekly_df,
        per_user_df=per_user_df,
        per_module_df=per_module_df,
        per_track_df=per_track_df,
    )


def _to_int(value: object) -> int:
    if isinstance(value, (int, float, str)):
        try:
            return int(value)
        except ValueError:
            return 0
    return 0
