from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd


TABLE_FILES = {
    "users": "users.csv",
    "certification_tracks": "certification_tracks.csv",
    "learning_paths": "learning_paths.csv",
    "modules": "modules.csv",
    "module_progress": "module_progress.csv",
    "time_entries": "time_entries.csv",
}


def _create_connection(data_dir: Path) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(database=":memory:")
    for table_name, filename in TABLE_FILES.items():
        csv_path = data_dir / filename
        escaped_path = str(csv_path).replace("\\", "/").replace("'", "''")
        conn.execute(
            f"CREATE VIEW {table_name} AS "
            f"SELECT * FROM read_csv_auto('{escaped_path}', HEADER=TRUE);"
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
    for table_name, filename in TABLE_FILES.items():
        query = f"SELECT COUNT(*) AS row_count FROM {table_name};"
        row_count = query_scalar(data_dir, query)
        counts[filename] = _to_int(row_count, -1)
    return counts


def _to_int(value: object, fallback: int) -> int:
    try:
        if isinstance(value, (int, float, str)):
            return int(value)
    except (TypeError, ValueError):
        pass
    return fallback
