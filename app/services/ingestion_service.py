from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path
from typing import Mapping
from uuid import uuid4

from app.models.schemas import ModuleProgressInput, TimeEntryInput


def _append_csv_row(csv_path: Path, row: Mapping[str, object]) -> None:
    with csv_path.open("r", newline="", encoding="utf-8") as read_file:
        reader = csv.reader(read_file)
        headers = next(reader)

    with csv_path.open("a", newline="", encoding="utf-8") as write_file:
        writer = csv.DictWriter(write_file, fieldnames=headers)
        writer.writerow(row)


def append_time_entry(data_dir: Path, time_entry: TimeEntryInput) -> None:
    time_entry.validate()
    now_iso = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    row = {
        "entry_id": str(uuid4()),
        "user_id": time_entry.user_id,
        "track_id": time_entry.track_id,
        "module_id": time_entry.module_id or "",
        "minutes_spent": time_entry.minutes_spent,
        "entry_date": time_entry.entry_date.isoformat(),
        "created_at": now_iso,
    }
    _append_csv_row(data_dir / "time_entries.csv", row)


def append_module_progress(data_dir: Path, progress_input: ModuleProgressInput) -> None:
    progress_input.validate()
    row = {
        "entry_id": str(uuid4()),
        "user_id": progress_input.user_id,
        "module_id": progress_input.module_id,
        "status": progress_input.status.value,
        "updated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }
    _append_csv_row(data_dir / "module_progress.csv", row)
