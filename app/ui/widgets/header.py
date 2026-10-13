import streamlit as st

from app.ui.components import wordmark
from app.ui.view import DossierView


def header(screen: DossierView) -> bool:
    """The wordmark row. Returns True when the person pressed `Read another file`."""
    left, right = st.columns([3, 1])
    with left:
        st.markdown(wordmark(screen.filename, screen.paper_count, screen.tier), unsafe_allow_html=True)
    with right:
        return st.button("Read another file")
