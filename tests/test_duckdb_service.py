from __future__ import annotations

from pathlib import Path

from app.services.duckdb_service import count_rows_for_curated_csvs
from scripts.bootstrap_data import bootstrap_curated_csvs


def test_count_rows_for_curated_csvs_handles_empty_module_progress_file(tmp_path: Path) -> None:
    data_dir = tmp_path / "curated"
    bootstrap_curated_csvs(data_dir)

    # Reproduce a corrupted/empty file state seen after local manual edits.
    (data_dir / "module_progress.csv").write_text("", encoding="utf-8")

    counts = count_rows_for_curated_csvs(data_dir)

    assert counts["module_progress.csv"] == 0

