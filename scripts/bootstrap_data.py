from __future__ import annotations

import csv
from pathlib import Path


CSV_HEADERS: dict[str, list[str]] = {
    "users.csv": ["user_id", "display_name", "active"],
    "certification_tracks.csv": ["track_id", "provider", "track_name", "exam_code"],
    "learning_paths.csv": ["path_id", "track_id", "path_name", "provider_url"],
    "modules.csv": ["module_id", "path_id", "track_id", "module_name", "provider_url", "module_order"],
    "module_progress.csv": ["entry_id", "user_id", "module_id", "status", "updated_at"],
    "time_entries.csv": [
        "entry_id",
        "user_id",
        "track_id",
        "module_id",
        "minutes_spent",
        "entry_date",
        "created_at",
    ],
}


def bootstrap_curated_csvs(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    for filename, headers in CSV_HEADERS.items():
        csv_path = data_dir / filename
        if csv_path.exists():
            continue
        with csv_path.open("w", newline="", encoding="utf-8") as file_obj:
            writer = csv.writer(file_obj)
            writer.writerow(headers)


if __name__ == "__main__":
    bootstrap_curated_csvs(Path("data/curated"))
