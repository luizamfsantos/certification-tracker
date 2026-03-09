from __future__ import annotations

import csv
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


DEFAULT_CATALOG_API_URL = "https://learn.microsoft.com/api/catalog/?type=learningPaths&product=azure&locale=en-us"


@dataclass(frozen=True)
class ImportSummary:
    exam_code: str
    fetched_items: int
    tracks_upserted: int
    learning_paths_upserted: int
    modules_upserted: int
    track_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def fetch_catalog_items(
    api_url: str = DEFAULT_CATALOG_API_URL,
    retries: int = 3,
    timeout_seconds: int = 30,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    next_url: str | None = api_url
    seen_urls: set[str] = set()

    while next_url:
        if next_url in seen_urls:
            break
        seen_urls.add(next_url)
        payload = _request_json(next_url, retries=retries, timeout_seconds=timeout_seconds)
        page_items, next_url = _extract_items_and_next(payload, current_url=next_url)
        items.extend(page_items)

    return items


def import_catalog_to_csv(
    data_dir: Path,
    exam_code: str,
    api_url: str = DEFAULT_CATALOG_API_URL,
    retries: int = 3,
    timeout_seconds: int = 30,
    catalog_items: list[dict[str, Any]] | None = None,
) -> ImportSummary:
    normalized_exam = exam_code.strip().lower()
    if not normalized_exam:
        raise ValueError("exam_code is required")

    items = catalog_items if catalog_items is not None else fetch_catalog_items(api_url, retries, timeout_seconds)
    track_row, path_rows, module_rows = map_catalog_to_rows(items, normalized_exam)

    tracks_upserted = upsert_csv_rows(data_dir / "certification_tracks.csv", "track_id", [track_row])
    learning_paths_upserted = upsert_csv_rows(data_dir / "learning_paths.csv", "path_id", path_rows)
    modules_upserted = upsert_csv_rows(data_dir / "modules.csv", "module_id", module_rows)

    return ImportSummary(
        exam_code=normalized_exam,
        fetched_items=len(items),
        tracks_upserted=tracks_upserted,
        learning_paths_upserted=learning_paths_upserted,
        modules_upserted=modules_upserted,
        track_id=track_row["track_id"],
    )


def map_catalog_to_rows(
    catalog_items: list[dict[str, Any]],
    exam_code: str,
) -> tuple[dict[str, str], list[dict[str, str]], list[dict[str, str]]]:
    normalized_exam = exam_code.strip().lower()
    if not normalized_exam:
        raise ValueError("exam_code is required")

    track_id = normalized_exam
    certification_title = _find_certification_title(catalog_items, normalized_exam)
    track_name = certification_title or f"{normalized_exam.upper()} Certification Track"
    track_row = {
        "track_id": track_id,
        "provider": "microsoft",
        "track_name": track_name,
        "exam_code": normalized_exam.upper(),
    }

    learning_path_items = [
        item
        for item in catalog_items
        if _looks_like_type(item, "learningpath") and _is_related_to_exam(item, normalized_exam)
    ]

    module_items = [item for item in catalog_items if _looks_like_type(item, "module")]
    module_item_by_id = {_entry_id(item, "mod"): item for item in module_items}

    path_rows: list[dict[str, str]] = []
    path_module_refs: dict[str, list[str]] = {}

    for path_item in learning_path_items:
        path_id = _entry_id(path_item, "lp")
        path_rows.append(
            {
                "path_id": path_id,
                "track_id": track_id,
                "path_name": _entry_title(path_item),
                "provider_url": _entry_url(path_item),
            }
        )
        path_module_refs[path_id] = _extract_related_ids(path_item)

    selected_module_ids: set[str] = set()
    selected_modules_by_path: dict[str, list[str]] = {path_id: [] for path_id in path_module_refs}
    for path_id, refs in path_module_refs.items():
        for ref in refs:
            if ref in module_item_by_id:
                selected_module_ids.add(ref)
                selected_modules_by_path[path_id].append(ref)

    for module_entry in module_items:
        module_id = _entry_id(module_entry, "mod")
        if _is_related_to_exam(module_entry, normalized_exam):
            selected_module_ids.add(module_id)

    if not path_rows:
        fallback_path_id = f"lp-{track_id}-general"
        path_rows.append(
            {
                "path_id": fallback_path_id,
                "track_id": track_id,
                "path_name": f"{track_name} - General",
                "provider_url": "",
            }
        )
        selected_modules_by_path[fallback_path_id] = []

    path_id_by_module: dict[str, str] = {}
    for path_id, module_ids in selected_modules_by_path.items():
        for module_id in module_ids:
            path_id_by_module.setdefault(module_id, path_id)

    default_path_id = path_rows[0]["path_id"]
    module_rows: list[dict[str, str]] = []
    path_order_counter: dict[str, int] = {}

    for module_id in sorted(selected_module_ids):
        module_item: dict[str, Any] | None = module_item_by_id.get(module_id)
        if not module_item:
            continue
        path_id = path_id_by_module.get(module_id, default_path_id)
        path_order_counter[path_id] = path_order_counter.get(path_id, 0) + 1
        module_rows.append(
            {
                "module_id": module_id,
                "path_id": path_id,
                "track_id": track_id,
                "module_name": _entry_title(module_item),
                "provider_url": _entry_url(module_item),
                "module_order": str(path_order_counter[path_id]),
            }
        )

    dedup_paths = {row["path_id"]: row for row in path_rows}
    dedup_modules = {row["module_id"]: row for row in module_rows}
    return track_row, list(dedup_paths.values()), list(dedup_modules.values())


def upsert_csv_rows(csv_path: Path, key_field: str, rows: list[dict[str, str]]) -> int:
    if not rows:
        return 0
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    with csv_path.open("r", newline="", encoding="utf-8") as read_file:
        reader = csv.DictReader(read_file)
        fieldnames = reader.fieldnames or []
        existing_rows = list(reader)

    by_key: dict[str, dict[str, str]] = {}
    ordered_keys: list[str] = []
    for row in existing_rows:
        key = row.get(key_field, "")
        if not key:
            continue
        ordered_keys.append(key)
        by_key[key] = row

    changed = 0
    for incoming in rows:
        key = incoming.get(key_field, "")
        if not key:
            continue
        normalized = {name: str(incoming.get(name, "")) for name in fieldnames}
        if key in by_key:
            if by_key[key] != normalized:
                by_key[key] = normalized
                changed += 1
        else:
            by_key[key] = normalized
            ordered_keys.append(key)
            changed += 1

    with csv_path.open("w", newline="", encoding="utf-8") as write_file:
        writer = csv.DictWriter(write_file, fieldnames=fieldnames)
        writer.writeheader()
        for key in ordered_keys:
            writer.writerow(by_key[key])

    return changed


def _request_json(url: str, retries: int, timeout_seconds: int) -> dict[str, Any] | list[Any]:
    attempt = 0
    while True:
        try:
            request = Request(url, headers={"User-Agent": "certification-tracker/0.1"})
            with urlopen(request, timeout=timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except (URLError, HTTPError, TimeoutError, json.JSONDecodeError):
            attempt += 1
            if attempt >= retries:
                raise
            time.sleep(min(2**attempt, 5))


def _extract_items_and_next(
    payload: dict[str, Any] | list[Any],
    current_url: str,
) -> tuple[list[dict[str, Any]], str | None]:
    if isinstance(payload, list):
        entries = [item for item in payload if isinstance(item, dict)]
        return entries, None

    items: list[dict[str, Any]] = []
    for key in ("items", "results", "value"):
        value = payload.get(key)
        if isinstance(value, list):
            items = [item for item in value if isinstance(item, dict)]
            break

    if not items:
        nested_items = payload.get("modules")
        if isinstance(nested_items, list):
            items = [item for item in nested_items if isinstance(item, dict)]

    next_link = None
    for key in ("nextLink", "next", "@odata.nextLink"):
        if isinstance(payload.get(key), str):
            next_link = payload[key]
            break

    if isinstance(next_link, str) and next_link:
        next_link = urljoin(current_url, next_link)

    return items, next_link


def _looks_like_type(item: dict[str, Any], kind: str) -> bool:
    type_value = str(item.get("type", "")).lower().replace("-", "").replace("_", "")
    return kind in type_value


def _is_related_to_exam(item: dict[str, Any], exam_code: str) -> bool:
    haystack = json.dumps(item, ensure_ascii=True).lower()
    return exam_code.lower() in haystack


def _entry_id(item: dict[str, Any], prefix: str) -> str:
    raw = str(
        item.get("uid")
        or item.get("id")
        or item.get("url")
        or item.get("title")
        or item.get("name")
        or ""
    ).strip()
    slug = raw.lower().replace("https://", "").replace("http://", "").strip("/")
    for token in ("learn.microsoft.com/", "training/", "modules/", "paths/"):
        slug = slug.replace(token, "")
    slug = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in slug)
    slug = "-".join(part for part in slug.split("-") if part)
    return slug if slug else f"{prefix}-unknown"


def _entry_title(item: dict[str, Any]) -> str:
    value = item.get("title") or item.get("name") or item.get("uid") or "Untitled"
    return str(value).strip()


def _entry_url(item: dict[str, Any]) -> str:
    value = item.get("url") or item.get("link") or ""
    return str(value).strip()


def _extract_related_ids(item: dict[str, Any]) -> list[str]:
    related: list[str] = []
    candidate_keys = ("modules", "children", "moduleUids", "moduleIds", "items")
    for key in candidate_keys:
        value = item.get(key)
        if isinstance(value, list):
            for entry in value:
                if isinstance(entry, str):
                    related.append(_entry_id({"uid": entry}, "mod"))
                elif isinstance(entry, dict):
                    related.append(_entry_id(entry, "mod"))
    return related


def _find_certification_title(catalog_items: list[dict[str, Any]], exam_code: str) -> str | None:
    for item in catalog_items:
        if _looks_like_type(item, "certification") and _is_related_to_exam(item, exam_code):
            return _entry_title(item)
    return None
