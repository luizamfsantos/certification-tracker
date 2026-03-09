from __future__ import annotations

import streamlit as st

from app.config import load_config
from app.services.metrics_service import get_date_bounds, get_weekly_study_sessions_by_user


def main() -> None:
    config = load_config()
    st.set_page_config(page_title="Certification Tracker", layout="wide")
    st.title("Certification Tracker")
    st.caption("Use the left sidebar to open Dashboard and Data Entry pages.")

    st.subheader("This Week")
    _, max_date = get_date_bounds(config.data_dir)
    sessions_df = get_weekly_study_sessions_by_user(config.data_dir, max_date)
    if sessions_df.empty:
        st.info("No users found.")
    else:
        for row in sessions_df.itertuples(index=False):
            label = f"{row.display_name} studied {int(row.sessions)} time(s) this week."
            if int(row.sessions) > 0:
                st.success(label)
            else:
                st.info(label)

    st.info("Next: open `01_dashboard` for analytics and `02_data_entry` to update tracker CSVs.")


if __name__ == "__main__":
    main()
