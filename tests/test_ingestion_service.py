from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

from app.models.enums import ModuleStatus
from app.models.schemas import ModuleProgressInput, TimeEntryInput
from app.services.ingestion_service import append_module_progress, append_time_entry


FIXTURE_MAP = {
    "sample_users.csv": "users.csv",
    "sample_certification_tracks.csv": "certification_tracks.csv",
    "sample_learning_paths.csv": "learning_paths.csv",
    "sample_modules.csv": "modules.csv",
    "sample_module_progress.csv": "module_progress.csv",
    "sample_time_entries.csv": "time_entries.csv",
}


def _seed_data_dir(data_dir: Path) -> None:
    fixture_dir = Path(__file__).parent / "fixtures"
    data_dir.mkdir(parents=True, exist_ok=True)
    for fixture_name, target_name in FIXTURE_MAP.items():
        shutil.copyfile(fixture_dir / fixture_name, data_dir / target_name)


def test_append_time_and_progress_entries(tmp_path: Path) -> None:
    data_dir = tmp_path / "curated"
    _seed_data_dir(data_dir)

    append_time_entry(
        data_dir,
        TimeEntryInput(
            user_id="u1",
            track_id="az-104",
            module_id="mod-governance",
            minutes_spent=25,
            entry_date=date(2026, 3, 8),
        ),
    )
    append_module_progress(
        data_dir,
        ModuleProgressInput(
            user_id="u1",
            module_id="mod-governance",
            status=ModuleStatus.SEEN,
        ),
    )

    time_lines = (data_dir / "time_entries.csv").read_text(encoding="utf-8").strip().splitlines()
    progress_lines = (data_dir / "module_progress.csv").read_text(encoding="utf-8").strip().splitlines()
    assert len(time_lines) == 9
    assert len(progress_lines) == 10
