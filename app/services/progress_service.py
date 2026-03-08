from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from app.models.enums import ModuleStatus
from app.services.duckdb_service import query_df, query_scalar
from app.services.metrics_service import ALL_OPTION


STATUS_SCORE_CASE = (
    "CASE status "
    f"WHEN '{ModuleStatus.NOT_SEEN.value}' THEN 0.0 "
    f"WHEN '{ModuleStatus.SEEN.value}' THEN 0.5 "
    f"WHEN '{ModuleStatus.MASTERED.value}' THEN 1.0 "
    "ELSE 0.0 END"
)


@dataclass(frozen=True)
class ProgressMetricsResult:
    completion_pct: float
    status_distribution_df: pd.DataFrame
    progress_bar_df: pd.DataFrame


def _build_coverage_cte(user_id: str | None, track_id: str | None) -> tuple[str, list[object]]:
    filters = ["1=1"]
    params: list[object] = []

    if user_id and user_id != ALL_OPTION:
        filters.append("u.user_id = ?")
        params.append(user_id)
    if track_id and track_id != ALL_OPTION:
        filters.append("m.track_id = ?")
        params.append(track_id)

    filter_sql = " AND ".join(filters)
    cte_sql = f"""
    WITH latest_status AS (
      SELECT user_id, module_id, status
      FROM (
        SELECT
          user_id,
          module_id,
          status,
          updated_at,
          ROW_NUMBER() OVER (PARTITION BY user_id, module_id ORDER BY updated_at DESC) AS rn
        FROM module_progress
      )
      WHERE rn = 1
    ),
    coverage AS (
      SELECT
        u.user_id,
        u.display_name,
        m.module_id,
        m.track_id,
        m.path_id,
        lp.path_name,
        ct.track_name,
        COALESCE(ls.status, '{ModuleStatus.NOT_SEEN.value}') AS status
      FROM users u
      CROSS JOIN modules m
      LEFT JOIN latest_status ls
        ON ls.user_id = u.user_id AND ls.module_id = m.module_id
      LEFT JOIN learning_paths lp
        ON lp.path_id = m.path_id
      LEFT JOIN certification_tracks ct
        ON ct.track_id = m.track_id
      WHERE {filter_sql}
    )
    """
    return cte_sql, params


def _with_missing_status_rows(status_df: pd.DataFrame) -> pd.DataFrame:
    expected = [
        ModuleStatus.NOT_SEEN.value,
        ModuleStatus.SEEN.value,
        ModuleStatus.MASTERED.value,
    ]
    existing = set(status_df["status"].tolist()) if not status_df.empty else set()
    rows = [{"status": status, "count": 0} for status in expected if status not in existing]
    if rows:
        status_df = pd.concat([status_df, pd.DataFrame(rows)], ignore_index=True)
    return status_df.sort_values("status").reset_index(drop=True)


def get_progress_metrics(data_dir: Path, user_id: str | None, track_id: str | None) -> ProgressMetricsResult:
    coverage_cte, params = _build_coverage_cte(user_id, track_id)

    completion_query = f"{coverage_cte} SELECT ROUND(AVG({STATUS_SCORE_CASE}) * 100.0, 2) FROM coverage;"
    completion_pct = _to_float(query_scalar(data_dir, completion_query, params))

    status_query = f"{coverage_cte} SELECT status, COUNT(*) AS count FROM coverage GROUP BY 1;"
    status_distribution_df = _with_missing_status_rows(query_df(data_dir, status_query, params))

    if user_id and user_id != ALL_OPTION:
        bar_query = (
            f"{coverage_cte} "
            f"SELECT path_name AS label, ROUND(AVG({STATUS_SCORE_CASE}) * 100.0, 2) AS completion_pct "
            "FROM coverage GROUP BY 1 ORDER BY 2 DESC, 1;"
        )
    else:
        bar_query = (
            f"{coverage_cte} "
            f"SELECT display_name AS label, ROUND(AVG({STATUS_SCORE_CASE}) * 100.0, 2) AS completion_pct "
            "FROM coverage GROUP BY 1 ORDER BY 2 DESC, 1;"
        )
    progress_bar_df = query_df(data_dir, bar_query, params)

    return ProgressMetricsResult(
        completion_pct=completion_pct,
        status_distribution_df=status_distribution_df,
        progress_bar_df=progress_bar_df,
    )


def _to_float(value: object) -> float:
    if isinstance(value, (int, float, str)):
        try:
            return float(value)
        except ValueError:
            return 0.0
    return 0.0
