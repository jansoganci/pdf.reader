import streamlit as st

from app.service import (
    correct_field,
    export_dossier,
    get_dossier,
    mark_export_with_errors,
    merge_document,
    page_image,
    set_manual,
    split_document,
)
from app.ui import state, view, widgets
from app.ui.components import banner, plain, summary_card


@st.cache_data(show_spinner=False)
def _cached_page_image(dossier_id: str, page_number: int) -> bytes | None:
    return page_image(dossier_id, page_number)


def render(dossier_id: str) -> None:
    """Check one dossier: header, export, state, totals, then one tab per paper."""
    dossier = get_dossier(dossier_id)
    if dossier is None or not dossier.documents:
        st.info("This file could not be opened.")
        st.stop()

    screen = view.build(dossier)

    if widgets.header(screen):
        state.go_home()
    file_typed = widgets.strip(dossier.manual)

    st.write("")
    _export_area(dossier, screen)

    st.markdown(banner(screen.tier, screen.banner_text), unsafe_allow_html=True)
    if st.button("Hide passed checks" if state.show_passed() else "Show passed checks"):
        state.toggle_show_passed()
        st.rerun()

    if screen.totals:
        cards = st.columns(len(screen.totals))
        for column, cell in zip(cards, screen.totals):
            column.markdown(summary_card(cell.label, cell.amount, cell.sub, cell.needs_check), unsafe_allow_html=True)

    st.write("")
    tabs = st.tabs([paper.tab_label for paper in screen.papers])
    for tab, paper in zip(tabs, screen.papers):
        with tab:
            _paper_tab(dossier, paper, file_typed)


def _export_area(dossier, screen: view.DossierView) -> None:
    with st.container():
        st.caption("Export")
        if screen.blocking_count and not dossier.export_with_errors:
            if widgets.export_override():
                mark_export_with_errors(dossier.id, True)
                st.rerun()
            return
        try:
            csv_path = export_dossier(dossier.id, "fields_csv")
            json_path = export_dossier(dossier.id, "json")
        except PermissionError:
            return
        widgets.export_buttons(csv_path.read_bytes(), json_path.read_bytes())


def _paper_tab(dossier, paper: view.PaperView, file_typed: dict[str, str]) -> None:
    st.subheader(paper.title)
    st.markdown(plain(paper.subline), unsafe_allow_html=True)

    preview, fields = st.columns([2, 1], gap="large")
    with preview:
        widgets.page_viewer(paper, lambda page: _cached_page_image(dossier.id, page))
    with fields:
        header = st.columns([1.3, 1.6, 1.5])
        header[0].caption("Field")
        header[1].caption("Value")
        header[2].caption("Printed text")
        result = widgets.paper_form(paper, dossier.manual)
        if result is not None:
            set_manual(dossier.id, {**file_typed, **result.paper_typed, **result.line_typed})
            for field_key, text in result.corrections.items():
                correct_field(dossier.id, paper.id, field_key, text)
            st.rerun()

    widgets.check_list(paper)

    action = widgets.join_split(paper)
    if action is not None:
        if action.kind == "join":
            merge_document(dossier.id, paper.id)
        else:
            split_document(dossier.id, paper.id, action.after_page)
        st.rerun()
