import streamlit as st

from app.ui import state
from app.ui.components import banner


def render() -> None:
    """Choose a PDF. Nothing from an earlier file is shown."""
    st.header("Would you like to read a new import file?")
    st.write("Choose a PDF, then click Read. Nothing from an earlier file is shown here.")
    uploaded = st.file_uploader("Import PDF", type=["pdf"])
    if st.button("Read this PDF", type="primary"):
        if uploaded is None:
            st.markdown(banner("warn", "Choose a PDF first."), unsafe_allow_html=True)
        else:
            state.set_pending(uploaded.name, uploaded.getvalue())
            st.rerun()
