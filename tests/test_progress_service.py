from __future__ import annotations

import shutil
from pathlib import Path

from app.services.metrics_service import ALL_OPTION
from app.services.progress_service import get_progress_metrics


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


def test_progress_metrics_latest_status_and_completion(tmp_path: Path) -> None:
    data_dir = tmp_path / "curated"
    _seed_data_dir(data_dir)

    result = get_progress_metrics(
        data_dir=data_dir,
        user_id=ALL_OPTION,
        track_id="az-104",
    )

    assert result.completion_pct == 43.75
    status_counts = {row["status"]: int(row["count"]) for _, row in result.status_distribution_df.iterrows()}
    assert status_counts["mastered"] == 2
    assert status_counts["seen"] == 3
    assert status_counts["not_seen"] == 3
