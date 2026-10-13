import streamlit as st

from app.ui import state


def export_override() -> bool:
    """Shown while errors block the download. True when the person chose to download anyway."""
    return st.checkbox("Download anyway — errors are not fixed yet", key=state.ALLOW_EXPORT_KEY)


def export_buttons(csv: bytes, json: bytes) -> None:
    columns = st.columns([1, 1, 4])
    columns[0].download_button("Download CSV", csv, file_name="fields.csv")
    columns[1].download_button("Download JSON", json, file_name="import-file.json", type="primary")
