from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from app.services.catalog_import_service import import_catalog_to_csv, map_catalog_to_rows, _parse_json_response
from scripts.bootstrap_data import bootstrap_curated_csvs


def _load_catalog_fixture() -> list[dict[str, object]]:
    fixture_path = Path(__file__).parent / "fixtures" / "sample_catalog_api_response.json"
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    return payload["items"]


def test_map_catalog_to_rows_filters_and_relates_items() -> None:
    items = _load_catalog_fixture()
    track_row, path_rows, module_rows = map_catalog_to_rows(items, "AZ-104")

    assert track_row["track_id"] == "az-104"
    assert "AZ-104" in track_row["track_name"].upper()
    assert len(path_rows) == 1
    assert len(module_rows) == 2
    assert all(row["track_id"] == "az-104" for row in module_rows)
    assert all("az-900" not in row["module_name"].lower() for row in module_rows)


def test_import_catalog_to_csv_is_idempotent(tmp_path: Path) -> None:
    data_dir = tmp_path / "curated"
    bootstrap_curated_csvs(data_dir)
    items = _load_catalog_fixture()

    first = import_catalog_to_csv(data_dir, "AZ-104", catalog_items=items)
    second = import_catalog_to_csv(data_dir, "AZ-104", catalog_items=items)

    assert first.tracks_upserted == 1
    assert first.learning_paths_upserted == 1
    assert first.modules_upserted == 2
    assert second.tracks_upserted == 0
    assert second.learning_paths_upserted == 0
    assert second.modules_upserted == 0

    with (data_dir / "modules.csv").open("r", encoding="utf-8", newline="") as file_obj:
        rows = list(csv.DictReader(file_obj))
    assert len(rows) == 2


def test_parse_json_response_supports_utf8_bom() -> None:
    body = b"\xef\xbb\xbf{\"items\":[]}"
    payload = _parse_json_response(body, "application/json; charset=utf-8", "https://learn.microsoft.com/api/catalog/")
    assert isinstance(payload, dict)
    assert payload["items"] == []


def test_parse_json_response_rejects_html() -> None:
    html = b"<!DOCTYPE html><html><body>not json</body></html>"
    with pytest.raises(ValueError, match="Expected JSON"):
        _parse_json_response(html, "text/html; charset=utf-8", "https://learn.microsoft.com/api/catalog/")
