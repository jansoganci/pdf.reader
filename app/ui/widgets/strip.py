import streamlit as st

from app.ui import state
from app.ui.lang import t
from app.ui.words import FILE_MANUAL, manual_label


def strip(manual: dict[str, str]) -> dict[str, str]:
    """The two values typed once per file (order number, exchange rate). Returns what is typed."""
    st.markdown('<div class="topbar-strip-marker"></div>', unsafe_allow_html=True)
    columns = st.columns([1, 1, 3], vertical_alignment="bottom")
    typed: dict[str, str] = {}
    for index, key in enumerate(FILE_MANUAL):
        typed[key] = columns[index].text_input(manual_label(key), value=manual.get(key, ""), key=state.file_key(key))
    columns[2].caption(t("strip.note"))
    return typed
