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
from app.ui.components import banner, plain, totals_strip


@st.cache_data(show_spinner=False)
def _cached_page_image(dossier_id: str, page_number: int) -> bytes | None:
    return page_image(dossier_id, page_number)


def render(dossier_id: str) -> None:
    """Check one dossier: header, export, state, totals, then one tab per paper."""
    dossier = get_dossier(dossier_id)
    if dossier is None or not dossier.documents:
        st.markdown(banner("crit", "This file could not be opened."), unsafe_allow_html=True)
        st.stop()

    screen = view.build(dossier)

    if widgets.header(screen):
        state.go_home()
    file_typed = widgets.strip(dossier.manual)

    st.write("")
    _export_area(dossier, screen)

    banner_column, passed_column = st.columns([5, 1], vertical_alignment="center")
    banner_column.markdown(banner(screen.tier, screen.banner_text), unsafe_allow_html=True)
    if passed_column.button(
        "Hide passed checks" if state.show_passed() else "Show passed checks", width="stretch"
    ):
        state.toggle_show_passed()
        st.rerun()

    if screen.totals:
        st.markdown(totals_strip(screen.totals), unsafe_allow_html=True)

    st.write("")
    tabs = st.tabs([paper.tab_label for paper in screen.papers])
    for tab, paper in zip(tabs, screen.papers):
        with tab:
            _paper_tab(dossier, paper, file_typed)


def _export_area(dossier, screen: view.DossierView) -> None:
    """The export row keeps one shape. While errors block it the buttons are disabled and the
    "download anyway" box sits beside them; ticking it lets the files through."""
    blocked = screen.blocking_count > 0
    csv = json = None
    if not blocked or dossier.export_with_errors:
        try:
            csv = export_dossier(dossier.id, "fields_csv").read_bytes()
            json = export_dossier(dossier.id, "json").read_bytes()
        except PermissionError:
            csv = json = None
    state.init_override(dossier.id, dossier.export_with_errors)
    with st.container():
        st.caption("Export")
        allowed = widgets.export_row(
            csv, json,
            show_override=blocked,
            overridden=dossier.export_with_errors,
            override_key=state.override_key(dossier.id),
        )
    if blocked and allowed != dossier.export_with_errors:
        mark_export_with_errors(dossier.id, allowed)
        st.rerun()


def _paper_tab(dossier, paper: view.PaperView, file_typed: dict[str, str]) -> None:
    st.subheader(paper.title)
    st.markdown(plain(paper.subline), unsafe_allow_html=True)

    preview, fields = st.columns([5, 6], gap="large")
    with preview:
        widgets.page_viewer(paper, lambda page: _cached_page_image(dossier.id, page))
    with fields:
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
