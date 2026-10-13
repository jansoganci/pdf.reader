from dataclasses import dataclass

import streamlit as st

from app.ui import state
from app.ui.view import PaperView


@dataclass(frozen=True)
class JoinSplitAction:
    kind: str  # "join" or "split"
    after_page: int | None = None  # for "split": the last page that stays in this paper


def join_split(paper: PaperView) -> JoinSplitAction | None:
    """Fix wrong page grouping. Returns what was pressed, or None."""
    if paper.position > 0 and st.button("Join with the paper above", key=state.join_key(paper.id)):
        return JoinSplitAction("join")
    if len(paper.page_numbers) > 1:
        after = st.selectbox(
            "Split after",
            list(paper.page_numbers[:-1]),
            format_func=lambda page: f"Page {page}",
            key=state.split_after_key(paper.id),
        )
        if st.button("Split after this page", key=state.split_key(paper.id)):
            return JoinSplitAction("split", int(after))
    return None
