from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.catalog_import_service import DEFAULT_CATALOG_API_URL, import_catalog_to_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Microsoft Learn catalog data into curated CSV files.")
    parser.add_argument("--exam-code", required=True, help="Exam code to filter catalog content (example: AZ-104)")
    parser.add_argument("--data-dir", default="data/curated", help="Path to curated CSV directory")
    parser.add_argument("--api-url", default=DEFAULT_CATALOG_API_URL, help="Microsoft Learn catalog API URL")
    parser.add_argument("--retries", type=int, default=3, help="HTTP retries")
    parser.add_argument("--timeout-seconds", type=int, default=30, help="HTTP timeout per request")
    args = parser.parse_args()

    summary = import_catalog_to_csv(
        data_dir=Path(args.data_dir),
        exam_code=args.exam_code,
        api_url=args.api_url,
        retries=args.retries,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(summary.to_dict(), indent=2))


if __name__ == "__main__":
    main()
