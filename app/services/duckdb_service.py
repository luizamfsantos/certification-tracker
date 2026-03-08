from __future__ import annotations

from pathlib import Path

import duckdb


REQUIRED_CSVS = [
    "users.csv",
    "certification_tracks.csv",
    "learning_paths.csv",
    "modules.csv",
    "module_progress.csv",
    "time_entries.csv",
]


def count_rows_for_curated_csvs(data_dir: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    conn = duckdb.connect(database=":memory:")
    for filename in REQUIRED_CSVS:
        csv_path = data_dir / filename
        if not csv_path.exists():
            counts[filename] = -1
            continue
        query = "SELECT COUNT(*) AS row_count FROM read_csv_auto(?, HEADER=TRUE);"
        row_count = conn.execute(query, [str(csv_path)]).fetchone()[0]
        counts[filename] = int(row_count)
    conn.close()
    return counts
