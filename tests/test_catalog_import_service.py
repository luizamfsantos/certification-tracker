from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path

import pytest

from app.services.catalog_import_service import (
    _extract_items_and_next,
    _parse_json_response,
    _request_json_via_curl,
    import_catalog_to_csv,
    map_catalog_to_rows,
)
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


def test_map_catalog_to_rows_uses_learning_path_module_refs_when_module_items_are_missing() -> None:
    items: list[dict[str, object]] = [
        {
            "uid": "learn.az-104-manage-storage",
            "type": "learningPath",
            "title": "AZ-104: Implement and manage storage in Azure",
            "url": "https://learn.microsoft.com/en-us/training/paths/az-104-manage-storage/",
            "modules": [
                "learn.wwl.configure-storage-accounts",
                "learn.wwl.configure-azure-files-file-sync",
            ],
        }
    ]

    _, path_rows, module_rows = map_catalog_to_rows(items, "AZ-104")

    assert len(path_rows) == 1
    assert [row["module_id"] for row in module_rows] == [
        "learn-wwl-configure-storage-accounts",
        "learn-wwl-configure-azure-files-file-sync",
    ]
    assert [row["module_order"] for row in module_rows] == ["1", "2"]
    assert module_rows[0]["module_name"] == "configure storage accounts"
    assert module_rows[0]["provider_url"] == ""


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
    body = b'\xef\xbb\xbf{"items":[]}'
    payload = _parse_json_response(
        body, "application/json; charset=utf-8", "https://learn.microsoft.com/api/catalog/"
    )
    assert isinstance(payload, dict)
    assert payload["items"] == []


def test_parse_json_response_rejects_html() -> None:
    html = b"<!DOCTYPE html><html><body>not json</body></html>"
    with pytest.raises(ValueError, match="Expected JSON"):
        _parse_json_response(
            html, "text/html; charset=utf-8", "https://learn.microsoft.com/api/catalog/"
        )


def test_extract_items_and_next_supports_learning_paths_key() -> None:
    payload = {
        "learningPaths": [
            {"uid": "learn.az-104-manage-storage"},
            {"uid": "learn.az-104-manage-compute-resources"},
        ],
        "nextLink": "/api/catalog/?type=learningPaths&product=azure&skip=2",
    }
    items, next_url = _extract_items_and_next(
        payload, "https://learn.microsoft.com/api/catalog/?type=learningPaths"
    )

    assert len(items) == 2
    assert (
        next_url
        == "https://learn.microsoft.com/api/catalog/?type=learningPaths&product=azure&skip=2"
    )


def test_request_json_via_curl_exports_raw_and_parses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    output_path = tmp_path / "catalog_raw.json"

    monkeypatch.setattr("app.services.catalog_import_service.shutil.which", lambda _: "curl.exe")

    def fake_run(
        command: list[str],
        *,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        out_index = command.index("--output")
        target = Path(command[out_index + 1])
        target.write_text('{"items":[{"uid":"x"}]}', encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("app.services.catalog_import_service.subprocess.run", fake_run)

    payload = _request_json_via_curl(
        url="https://learn.microsoft.com/api/catalog/",
        output_path=output_path,
        retries=3,
        timeout_seconds=15,
    )

    assert output_path.exists()
    assert isinstance(payload, dict)
    assert len(payload["items"]) == 1
    assert (
        output_path.read_text(encoding="utf-8")
        == '{\n  "items": [\n    {\n      "uid": "x"\n    }\n  ]\n}\n'
    )
