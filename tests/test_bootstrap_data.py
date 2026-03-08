from __future__ import annotations

from pathlib import Path

from scripts.bootstrap_data import CSV_HEADERS, bootstrap_curated_csvs


def test_bootstrap_curated_csvs_creates_all_files(tmp_path: Path) -> None:
    data_dir = tmp_path / "curated"
    bootstrap_curated_csvs(data_dir)

    for filename, headers in CSV_HEADERS.items():
        csv_path = data_dir / filename
        assert csv_path.exists()
        first_line = csv_path.read_text(encoding="utf-8").splitlines()[0]
        assert first_line == ",".join(headers)
