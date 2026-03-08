from __future__ import annotations

import streamlit as st


def render() -> None:
    st.set_page_config(page_title="Catalog Import", layout="wide")
    st.title("Catalog Import")
    st.info("Manual import workflow is planned. Script implementation comes in Phase 4.")


if __name__ == "__main__":
    render()
