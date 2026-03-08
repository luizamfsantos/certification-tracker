from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def render() -> None:
    st.set_page_config(page_title="Catalog Import", layout="wide")
    st.title("Catalog Import")
    st.info("Manual import workflow is planned. Script implementation comes in Phase 4.")


if __name__ == "__main__":
    render()
