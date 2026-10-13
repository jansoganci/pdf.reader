from collections.abc import Callable

import streamlit as st

from app.ui import state
from app.ui.components import page_label
from app.ui.view import PaperView


def page_viewer(paper: PaperView, image_for: Callable[[int], bytes | None]) -> None:
    """The scanned page of the open paper, with page buttons when it spans several.

    `image_for(page_number)` is given by the screen, so this widget never calls the service.
    """
    current_page = state.current_page(paper.id, paper.default_page, paper.page_numbers)
    st.markdown('<div class="sticky-preview"></div>', unsafe_allow_html=True)
    if not paper.page_numbers:
        return
    if len(paper.page_numbers) > 1:
        position = paper.page_numbers.index(current_page)
        nav_left, nav_label, nav_right = st.columns([1, 2, 1])
        if nav_left.button(
            "", icon=":material/chevron_left:", key=state.prev_key(paper.id),
            disabled=position == 0, width="stretch",
        ):
            state.set_page(paper.id, paper.page_numbers[position - 1])
            st.rerun()
        nav_label.markdown(page_label(current_page, position, len(paper.page_numbers)), unsafe_allow_html=True)
        if nav_right.button(
            "", icon=":material/chevron_right:", key=state.next_key(paper.id),
            disabled=position == len(paper.page_numbers) - 1, width="stretch",
        ):
            state.set_page(paper.id, paper.page_numbers[position + 1])
            st.rerun()
    image = image_for(current_page)
    if image:
        st.image(image, width="stretch")
