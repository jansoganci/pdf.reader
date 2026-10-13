import streamlit as st

from app.ui import state
from app.ui.components import banner
from app.ui.view import PaperView


def check_list(paper: PaperView) -> None:
    """The failed checks of one paper as banners, and the passed ones when the person asked."""
    for check in paper.failed_checks:
        st.markdown(banner(check.tier, check.text), unsafe_allow_html=True)
    if state.show_passed():
        for text in paper.passed_checks:
            st.caption(text)
