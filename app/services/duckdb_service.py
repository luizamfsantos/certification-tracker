from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import duckdb
import pandas as pd


@dataclass(frozen=True)
class TableConfig:
    filename: str
    headers: list[str]


TABLE_CONFIG = {
    "users": TableConfig(
        filename="users.csv",
        headers=["user_id", "display_name", "active"],
    ),
    "certification_tracks": TableConfig(
        filename="certification_tracks.csv",
        headers=["track_id", "provider", "track_name", "exam_code"],
    ),
    "learning_paths": TableConfig(
        filename="learning_paths.csv",
        headers=["path_id", "track_id", "path_name", "provider_url"],
    ),
    "modules": TableConfig(
        filename="modules.csv",
        headers=["module_id", "path_id", "track_id", "module_name", "provider_url", "module_order"],
    ),
    "module_progress": TableConfig(
        filename="module_progress.csv",
        headers=["entry_id", "user_id", "module_id", "status", "updated_at"],
    ),
    "time_entries": TableConfig(
        filename="time_entries.csv",
        headers=[
            "entry_id",
            "user_id",
            "track_id",
            "module_id",
            "minutes_spent",
            "entry_date",
            "created_at",
        ],
    ),
}


def _create_connection(data_dir: Path) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(database=":memory:")
    for table_name, config in TABLE_CONFIG.items():
        csv_path = data_dir / config.filename
        _ensure_csv_header(csv_path, config.headers)
        escaped_path = str(csv_path).replace("\\", "/").replace("'", "''")
        conn.execute(
            f"CREATE VIEW {table_name} AS "
            "SELECT * FROM read_csv("
            f"'{escaped_path}', "
            "header=TRUE, "
            "delim=',', "
            "quote='\"', "
            "escape='\"', "
            "ignore_errors=TRUE, "
            "null_padding=TRUE"
            ");"
        )
    return conn


def query_df(data_dir: Path, query: str, params: list[object] | None = None) -> pd.DataFrame:
    conn = _create_connection(data_dir)
    try:
        return conn.execute(query, params or []).fetchdf()
    finally:
        conn.close()


def query_scalar(data_dir: Path, query: str, params: list[object] | None = None) -> object:
    conn = _create_connection(data_dir)
    try:
        row = conn.execute(query, params or []).fetchone()
        return None if row is None else row[0]
    finally:
        conn.close()


def count_rows_for_curated_csvs(data_dir: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table_name, config in TABLE_CONFIG.items():
        query = f"SELECT COUNT(*) AS row_count FROM {table_name};"
        row_count = query_scalar(data_dir, query)
        counts[config.filename] = _to_int(row_count, -1)
    return counts


def _ensure_csv_header(csv_path: Path, expected_headers: list[str]) -> None:
    expected_header_line = ",".join(expected_headers)
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        _write_header_only(csv_path, expected_headers)
        return

    with csv_path.open("r", newline="", encoding="utf-8") as file_obj:
        reader = csv.reader(file_obj)
        first_row = next(reader, [])

    if not first_row:
        _write_header_only(csv_path, expected_headers)
        return

    normalized_first = ",".join(cell.strip() for cell in first_row)
    if normalized_first != expected_header_line:
        raise ValueError(
            f"CSV header mismatch for {csv_path}. "
            f"Expected: {expected_header_line}. Got: {normalized_first}"
        )


def _write_header_only(csv_path: Path, headers: list[str]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as file_obj:
        writer = csv.writer(file_obj)
        writer.writerow(headers)


def _to_int(value: object, fallback: int) -> int:
    try:
        if isinstance(value, (int, float, str)):
            return int(value)
    except (TypeError, ValueError):
        pass
    return fallback
