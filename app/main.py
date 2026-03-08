from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import load_config  # noqa: E402
from app.services.duckdb_service import count_rows_for_curated_csvs  # noqa: E402


def main() -> None:
    config = load_config()
    st.set_page_config(page_title="Certification Tracker", layout="wide")
    st.title("Certification Tracker")
    st.caption("Use the left sidebar to open Dashboard and Data Entry pages.")

    st.subheader("Environment")
    st.write(
        {
            "env": config.env,
            "data_dir": str(config.data_dir),
            "log_level": config.log_level,
        }
    )

    st.subheader("Curated CSV Status")
    counts = count_rows_for_curated_csvs(config.data_dir)
    st.dataframe(
        [{"file": name, "rows": rows} for name, rows in counts.items()],
        use_container_width=True,
    )
    st.info("Next: open `01_dashboard` for analytics and `02_data_entry` to update tracker CSVs.")


if __name__ == "__main__":
    main()
