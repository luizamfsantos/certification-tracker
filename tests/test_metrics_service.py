from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

from app.services.metrics_service import (
    ALL_OPTION,
    get_time_metrics,
    get_weekly_study_sessions_by_user,
)


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


def test_time_metrics_aggregations(tmp_path: Path) -> None:
    data_dir = tmp_path / "curated"
    _seed_data_dir(data_dir)

    result = get_time_metrics(
        data_dir=data_dir,
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 8),
        user_id=ALL_OPTION,
        track_id="az-104",
    )

    assert result.total_minutes == 245
    assert result.daily_minutes == 20
    assert result.weekly_minutes == 245
    assert result.daily_df["entry_date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2026-03-02",
        "2026-03-03",
        "2026-03-07",
        "2026-03-08",
    ]
    assert result.daily_df["minutes"].tolist() == [60, 75, 90, 20]
    assert set(result.per_user_df["user_name"].tolist()) == {"Alice", "Bob"}


def test_get_weekly_study_sessions_by_user(tmp_path: Path) -> None:
    data_dir = tmp_path / "curated"
    _seed_data_dir(data_dir)

    sessions_df = get_weekly_study_sessions_by_user(data_dir, date(2026, 3, 8))

    assert sessions_df["display_name"].tolist() == ["Alice", "Bob"]
    assert sessions_df["sessions"].tolist() == [3, 2]
