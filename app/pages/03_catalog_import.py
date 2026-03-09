from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.config import load_config
from app.services.catalog_import_service import DEFAULT_CATALOG_API_URL, import_catalog_to_csv


def render() -> None:
    st.set_page_config(page_title="Catalog Import", layout="wide")
    st.title("Catalog Import")
    st.caption("Import learning paths and modules using the Microsoft Learn Catalog API.")

    config = load_config()

    with st.form("catalog_import_form"):
        exam_code = st.text_input("Exam code", value="AZ-104").strip()
        api_url = st.text_input("API URL", value=DEFAULT_CATALOG_API_URL).strip()
        use_curl = st.checkbox("Use curl workaround (export raw, then parse)", value=True)
        raw_dir = st.text_input("Raw export directory", value="data/raw/microsoft_learn").strip()
        retries = st.number_input("Retries", min_value=1, max_value=10, value=3, step=1)
        timeout_seconds = st.number_input("Timeout (seconds)", min_value=5, max_value=120, value=30, step=5)
        submit = st.form_submit_button("Run import")

    if submit:
        if not exam_code:
            st.error("Exam code is required.")
            return
        try:
            with st.spinner("Importing catalog data..."):
                summary = import_catalog_to_csv(
                    data_dir=config.data_dir,
                    exam_code=exam_code,
                    api_url=api_url,
                    transport="curl" if use_curl else "urllib",
                    raw_dir=Path(raw_dir),
                    retries=int(retries),
                    timeout_seconds=int(timeout_seconds),
                )
            st.success("Catalog import completed.")
            st.json(summary.to_dict(), expanded=True)
        except Exception as exc:
            st.error(f"Catalog import failed: {exc}")


if __name__ == "__main__":
    render()
