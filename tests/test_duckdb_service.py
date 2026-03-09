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


def test_count_rows_for_curated_csvs_recovers_malformed_module_progress_file(tmp_path: Path) -> None:
    data_dir = tmp_path / "curated"
    bootstrap_curated_csvs(data_dir)

    malformed_csv = (
        'entry_id,user_id,module_id,status,updated_at\n'
        '"broken-row-with-unclosed-quote\n'
        "id-1,u1,mod-1,seen,2026-03-09T11:17:43Z\n"
    )
    (data_dir / "module_progress.csv").write_text(malformed_csv, encoding="utf-8")

    counts = count_rows_for_curated_csvs(data_dir)

    assert counts["module_progress.csv"] == 1
