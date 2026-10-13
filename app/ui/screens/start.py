import streamlit as st

from app.ui import state
from app.ui.components import banner
from app.ui.lang import t


def render() -> None:
    """Choose a PDF. Nothing from an earlier file is shown."""
    st.header(t("start.heading"))
    st.write(t("start.intro"))
    uploaded = st.file_uploader(t("start.uploader"), type=["pdf"])
    if st.button(t("start.read"), type="primary"):
        if uploaded is None:
            st.markdown(banner("warn", t("start.choose_first")), unsafe_allow_html=True)
        else:
            state.set_pending(uploaded.name, uploaded.getvalue())
            st.rerun()
