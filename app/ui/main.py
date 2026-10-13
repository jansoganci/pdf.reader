import streamlit as st

from app.pdf.render import PdfRejected
from app.service import (
    correct_field,
    export_dossier,
    get_dossier,
    mark_export_with_errors,
    merge_document,
    page_image,
    process_upload,
    set_manual,
    split_document,
)
from app.ui import state, view
from app.ui.components import (
    banner,
    field_label,
    group_title,
    page_label,
    plain,
    summary_card,
    wordmark,
)
from app.ui.theme import inject
from app.ui.words import FILE_MANUAL, LINE_MANUAL


@st.cache_data(show_spinner=False)
def _cached_page_image(dossier_id: str, page_number: int) -> bytes | None:
    return page_image(dossier_id, page_number)


st.set_page_config(page_title="Import file", layout="wide", initial_sidebar_state="collapsed")
inject()
state.init()


def _start_home() -> None:
    state.close_dossier()
    st.rerun()


pending = state.pending()
if pending:
    st.header("Reading the PDF")
    st.markdown(plain(f"{pending['name']} is being read now.", "body"), unsafe_allow_html=True)
    st.write("Please wait. This takes about a minute. Do not close this page.")
    with st.status("Sending the PDF to be read…", expanded=True) as status:
        try:
            dossier = process_upload(pending["data"], pending["name"], use_cache=False)
        except PdfRejected as exc:
            state.clear_pending()
            st.error(exc.message)
            if st.button("Back"):
                _start_home()
            st.stop()
        except RuntimeError as exc:
            state.clear_pending()
            st.error(str(exc))
            if st.button("Back"):
                _start_home()
            st.stop()
        status.update(label="Reading finished", state="complete")
    state.clear_pending()
    state.open_dossier(dossier.id)
    st.rerun()

dossier_id = state.dossier_id()
if not dossier_id:
    st.header("Would you like to read a new import file?")
    st.write("Choose a PDF, then click Read. Nothing from an earlier file is shown here.")
    uploaded = st.file_uploader("Import PDF", type=["pdf"])
    if st.button("Read this PDF", type="primary"):
        if uploaded is None:
            st.warning("Choose a PDF first.")
        else:
            state.set_pending(uploaded.name, uploaded.getvalue())
            st.rerun()
    st.stop()

dossier = get_dossier(dossier_id)
if dossier is None or not dossier.documents:
    st.info("This file could not be opened.")
    st.stop()

screen = view.build(dossier)

head_left, head_right = st.columns([3, 1])
with head_left:
    st.markdown(wordmark(screen.filename, screen.paper_count, screen.tier), unsafe_allow_html=True)
with head_right:
    if st.button("Read another file"):
        _start_home()

st.markdown('<div class="topbar-strip-marker"></div>', unsafe_allow_html=True)
strip_cols = st.columns([1, 1, 0.3, 4])
file_typed: dict[str, str] = {}
for index, (key, label) in enumerate(FILE_MANUAL):
    file_typed[key] = strip_cols[index].text_input(label, value=dossier.manual.get(key, ""), key=state.file_key(key))
strip_cols[2].markdown(
    '<span class="strip-info" title="Not on any page. Saved with the open paper\'s Save button below.">i</span>',
    unsafe_allow_html=True,
)

st.write("")
with st.container():
    st.caption("Export")
    if screen.blocking_count and not dossier.export_with_errors:
        allow = st.checkbox("Download anyway — errors are not fixed yet", key=state.ALLOW_EXPORT_KEY)
        if allow:
            mark_export_with_errors(dossier.id, True)
            st.rerun()
    else:
        try:
            csv_path = export_dossier(dossier.id, "fields_csv")
            json_path = export_dossier(dossier.id, "json")
        except PermissionError:
            csv_path = json_path = None
        if csv_path and json_path:
            export_cols = st.columns([1, 1, 4])
            export_cols[0].download_button("Download CSV", csv_path.read_bytes(), file_name="fields.csv")
            export_cols[1].download_button(
                "Download JSON", json_path.read_bytes(), file_name="import-file.json", type="primary"
            )

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
        st.subheader(paper.title)
        st.markdown(plain(paper.subline), unsafe_allow_html=True)

        current_page = state.current_page(paper.id, paper.default_page, paper.page_numbers)

        preview, fields = st.columns([2, 1], gap="large")
        with preview:
            st.markdown('<div class="sticky-preview"></div>', unsafe_allow_html=True)
            if paper.page_numbers:
                if len(paper.page_numbers) > 1:
                    position = paper.page_numbers.index(current_page)
                    nav_left, nav_label, nav_right = st.columns([1, 2, 1])
                    if nav_left.button(
                        "", icon=":material/chevron_left:", key=state.prev_key(paper.id),
                        disabled=position == 0, width="stretch",
                    ):
                        state.set_page(paper.id, paper.page_numbers[position - 1])
                        st.rerun()
                    nav_label.markdown(
                        page_label(current_page, position, len(paper.page_numbers)),
                        unsafe_allow_html=True,
                    )
                    if nav_right.button(
                        "", icon=":material/chevron_right:", key=state.next_key(paper.id),
                        disabled=position == len(paper.page_numbers) - 1, width="stretch",
                    ):
                        state.set_page(paper.id, paper.page_numbers[position + 1])
                        st.rerun()
                image = _cached_page_image(dossier.id, current_page)
                if image:
                    st.image(image, width="stretch")

        with fields:
            header = st.columns([1.3, 1.6, 1.5])
            header[0].caption("Field")
            header[1].caption("Value")
            header[2].caption("Printed text")

            with st.form(state.form_key(paper.id)):
                st.markdown(group_title("Copied from the page"), unsafe_allow_html=True)
                correction_inputs: dict[str, tuple[str, str]] = {}
                for row in paper.rows:
                    label, value_col, printed = st.columns([1.3, 1.6, 1.5])
                    label.markdown(field_label(row.label, row.needs_check), unsafe_allow_html=True)
                    new_value = value_col.text_input(
                        row.label,
                        value=row.value_text,
                        key=state.value_key(paper.id, row.key),
                        label_visibility="collapsed",
                    )
                    printed.markdown(plain(row.printed_text), unsafe_allow_html=True)
                    correction_inputs[row.key] = (row.value_text, new_value)

                line_typed: dict[str, str] = {}
                if paper.lines:
                    st.write("")
                    st.caption("Lines copied from the page")
                    for line in paper.lines:
                        if paper.line_codes:
                            line_left, line_tax, line_reason = st.columns([2.2, 1.15, 1.15])
                            line_left.markdown(plain(line.text, "body"), unsafe_allow_html=True)
                            for lk, ll in LINE_MANUAL:
                                store_key = view.line_store_key(paper.id, line.index, lk)
                                target = line_tax if lk == "tax_code" else line_reason
                                line_typed[store_key] = target.text_input(
                                    ll, value=dossier.manual.get(store_key, ""), key=state.line_key(store_key)
                                )
                        else:
                            st.markdown(plain(line.text, "body"), unsafe_allow_html=True)

                st.write("")
                st.markdown(group_title("You type"), unsafe_allow_html=True)
                st.caption("Not on the PDF. Leave a box empty if you do not have it yet.")
                for note in paper.typed_notes:
                    st.caption(note)
                paper_typed: dict[str, str] = {}
                manual_cols = st.columns(2)
                for index, (key, label) in enumerate(paper.typed_fields):
                    store_key = view.paper_store_key(paper.id, key)
                    paper_typed[store_key] = manual_cols[index % 2].text_input(
                        label, value=dossier.manual.get(store_key, ""), key=state.paper_key(store_key)
                    )

                submitted = st.form_submit_button("Save", type="primary")
                if submitted:
                    set_manual(dossier.id, {**file_typed, **paper_typed, **line_typed})
                    for field_key, (before, after) in correction_inputs.items():
                        if after != before:
                            correct_field(dossier.id, paper.id, field_key, after)
                    st.rerun()

        for check in paper.failed_checks:
            st.markdown(banner(check.tier, check.text), unsafe_allow_html=True)
        if state.show_passed():
            for text in paper.passed_checks:
                st.caption(text)

        if paper.position > 0 and st.button("Join with the paper above", key=state.join_key(paper.id)):
            merge_document(dossier.id, paper.id)
            st.rerun()
        if len(paper.page_numbers) > 1:
            after = st.selectbox(
                "Split after",
                list(paper.page_numbers[:-1]),
                format_func=lambda page: f"Page {page}",
                key=state.split_after_key(paper.id),
            )
            if st.button("Split after this page", key=state.split_key(paper.id)):
                split_document(dossier.id, paper.id, int(after))
                st.rerun()
