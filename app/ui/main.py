import streamlit as st

from app.models import DocumentRecord, Dossier
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
from app.ui.components import (
    TIER_WORDS,
    banner,
    field_label,
    group_title,
    page_label,
    plain,
    summary_card,
    wordmark,
)
from app.ui.theme import inject
from app.ui.words import (
    FILE_MANUAL,
    LINE_MANUAL,
    PAPER_MANUAL,
    check_sentence,
    field_name,
    issued_by,
    money_text,
    pages_text,
    paper_name,
    shown_keys,
    shown_value,
)

@st.cache_data(show_spinner=False)
def _cached_page_image(dossier_id: str, page_number: int) -> bytes | None:
    return page_image(dossier_id, page_number)


st.set_page_config(page_title="Import file", layout="wide", initial_sidebar_state="collapsed")
inject()

MONEY_KEYS = {
    "net_amount", "tax_amount", "total_amount", "fob_amount",
    "freight_amount", "customs_value", "insurance_amount",
}

def _currency(document: DocumentRecord, key: str) -> str | None:
    if key == "customs_value":
        return "MAD"
    if document.document_type == "customs_liquidation" and key in MONEY_KEYS:
        field = document.fields.get("currency")
        value = None if field is None else shown_value(field)
        return str(value) if value not in (None, "") else "MAD"
    field = document.fields.get("currency")
    if field is None:
        return None
    value = shown_value(field)
    return None if value in (None, "") else str(value)


def _display(document: DocumentRecord, key: str) -> str:
    field = document.fields.get(key)
    if field is None:
        return ""
    value = shown_value(field)
    if value in (None, ""):
        return ""
    if key in MONEY_KEYS:
        return money_text(value, _currency(document, key))
    if key == "exchange_rate":
        return str(value)
    return str(value)


def _headline_amount(document: DocumentRecord) -> str:
    for key in ("total_amount", "customs_value"):
        text = _display(document, key)
        if text:
            return text
    return ""


def _check_sentence(dossier: Dossier, item) -> str:
    names = []
    for document_id in item.fields:
        found = next((doc for doc in dossier.documents if doc.id == document_id), None)
        if found is not None:
            names.append(paper_name(found.document_type))
    paper = names[0] if len(names) == 1 else None
    if item.status == "passed":
        return f"{paper}: {item.message}" if paper else item.message
    return check_sentence(item.rule_id, item.message, paper)


def _tab_label(document: DocumentRecord) -> str:
    name = paper_name(document.document_type)
    needs_check = any(field.status == "review" for field in document.fields.values())
    return f"• {name}" if needs_check else name


def _default_page(document: DocumentRecord) -> int | None:
    """Open on the page a flagged field was actually read from. Fall back to
    the paper's first page when nothing needs a check."""
    if not document.page_numbers:
        return None
    for key in shown_keys(document):
        field = document.fields[key]
        if field.status == "review" and field.source_page in document.page_numbers:
            return field.source_page
    return document.page_numbers[0]


def _start_home() -> None:
    st.session_state.pop("dossier_id", None)
    st.rerun()


def _paper_manual_fields(document_type: str) -> list[tuple[str, str]]:
    fields = list(PAPER_MANUAL)
    if document_type == "broker_invoice":
        # Each service line gets its own tax code and reason code instead.
        fields = [(key, label) for key, label in fields if key not in ("tax_code", "reason_code")]
    if document_type in ("customs_declaration", "customs_liquidation"):
        fields = fields + [("sap_reference", "SAP reference")]
    return fields


if "show_passed" not in st.session_state:
    st.session_state["show_passed"] = False

pending = st.session_state.get("pending")
if pending:
    st.header("Reading the PDF")
    st.markdown(plain(f"{pending['name']} is being read now.", "body"), unsafe_allow_html=True)
    st.write("Please wait. This takes about a minute. Do not close this page.")
    with st.status("Sending the PDF to be read…", expanded=True) as status:
        try:
            dossier = process_upload(pending["data"], pending["name"], use_cache=False)
        except PdfRejected as exc:
            st.session_state.pop("pending", None)
            st.error(exc.message)
            if st.button("Back"):
                _start_home()
            st.stop()
        except RuntimeError as exc:
            st.session_state.pop("pending", None)
            st.error(str(exc))
            if st.button("Back"):
                _start_home()
            st.stop()
        status.update(label="Reading finished", state="complete")
    st.session_state.pop("pending", None)
    st.session_state["dossier_id"] = dossier.id
    st.rerun()

dossier_id = st.session_state.get("dossier_id")
if not dossier_id:
    st.header("Would you like to read a new import file?")
    st.write("Choose a PDF, then click Read. Nothing from an earlier file is shown here.")
    uploaded = st.file_uploader("Import PDF", type=["pdf"])
    if st.button("Read this PDF", type="primary"):
        if uploaded is None:
            st.warning("Choose a PDF first.")
        else:
            st.session_state["pending"] = {"name": uploaded.name, "data": uploaded.getvalue()}
            st.rerun()
    st.stop()

dossier = get_dossier(dossier_id)
if dossier is None or not dossier.documents:
    st.info("This file could not be opened.")
    st.stop()

failed = [item for item in dossier.validation if item.status == "failed"]
blocking = [item for item in failed if item.severity == "error"]

status_tier = "crit" if blocking else ("warn" if failed else "good")

head_left, head_right = st.columns([3, 1])
with head_left:
    st.markdown(wordmark(dossier.filename, len(dossier.documents), status_tier), unsafe_allow_html=True)
with head_right:
    if st.button("Read another file"):
        _start_home()

st.markdown('<div class="topbar-strip-marker"></div>', unsafe_allow_html=True)
strip_cols = st.columns([1, 1, 0.3, 4])
file_typed: dict[str, str] = {}
for index, (key, label) in enumerate(FILE_MANUAL):
    file_typed[key] = strip_cols[index].text_input(label, value=dossier.manual.get(key, ""), key=f"file-{key}")
strip_cols[2].markdown(
    '<span class="strip-info" title="Not on any page. Saved with the open paper\'s Save button below.">i</span>',
    unsafe_allow_html=True,
)

st.write("")
with st.container():
    st.caption("Export")
    if blocking and not dossier.export_with_errors:
        allow = st.checkbox("Download anyway — errors are not fixed yet", key="allow-export-with-errors")
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

if blocking:
    st.markdown(banner("crit", f"{len(blocking)} item(s) block the download until you check them."), unsafe_allow_html=True)
elif failed:
    st.markdown(banner("warn", f"{len(failed)} item(s) might need a second look before you download."), unsafe_allow_html=True)
else:
    st.markdown(banner("good", TIER_WORDS["good"] + "."), unsafe_allow_html=True)
if st.button("Hide passed checks" if st.session_state["show_passed"] else "Show passed checks"):
    st.session_state["show_passed"] = not st.session_state["show_passed"]
    st.rerun()

summary = []
for kind, label, key in (
    ("supplier_invoice", "Supplier invoice", "total_amount"),
    ("customs_declaration", "Customs value", "customs_value"),
    ("customs_liquidation", "Customs payment", "total_amount"),
    ("carrier_invoice", "Shipping invoice", "total_amount"),
):
    found = next((item for item in dossier.documents if item.document_type == kind), None)
    if found is None:
        continue
    field = found.fields.get(key)
    summary.append((label, _display(found, key) or "Not read", found, field is not None and field.status == "review", kind))

if summary:
    cards = st.columns(len(summary))
    for column, (label, amount, found, needs, kind) in zip(cards, summary):
        who = issued_by(found)
        if kind == "customs_declaration":
            sub = "Copied from the customs papers"
        elif who:
            sub = f"Issued by {who}"
        else:
            sub = ""
        column.markdown(summary_card(label, amount, sub, needs), unsafe_allow_html=True)

st.write("")
tabs = st.tabs([_tab_label(item) for item in dossier.documents])
for tab, document in zip(tabs, dossier.documents):
    with tab:
        st.subheader(paper_name(document.document_type))
        who = issued_by(document)
        amount = _headline_amount(document)
        st.markdown(plain(" · ".join(
            bit for bit in (
                pages_text(document.page_numbers),
                f"Issued by {who}" if who else "",
                amount,
            ) if bit
        )), unsafe_allow_html=True)

        page_state_key = f"page-{document.id}"
        current_page = st.session_state.get(page_state_key, _default_page(document))
        if current_page not in document.page_numbers:
            current_page = _default_page(document)

        preview, fields = st.columns([2, 1], gap="large")
        with preview:
            st.markdown('<div class="sticky-preview"></div>', unsafe_allow_html=True)
            if document.page_numbers:
                if len(document.page_numbers) > 1:
                    position = document.page_numbers.index(current_page)
                    nav_left, nav_label, nav_right = st.columns([1, 2, 1])
                    if nav_left.button(
                        "", icon=":material/chevron_left:", key=f"prev-{document.id}",
                        disabled=position == 0, width="stretch",
                    ):
                        st.session_state[page_state_key] = document.page_numbers[position - 1]
                        st.rerun()
                    nav_label.markdown(
                        page_label(current_page, position, len(document.page_numbers)),
                        unsafe_allow_html=True,
                    )
                    if nav_right.button(
                        "", icon=":material/chevron_right:", key=f"next-{document.id}",
                        disabled=position == len(document.page_numbers) - 1, width="stretch",
                    ):
                        st.session_state[page_state_key] = document.page_numbers[position + 1]
                        st.rerun()
                image = _cached_page_image(dossier.id, current_page)
                if image:
                    st.image(image, width="stretch")

        with fields:
            header = st.columns([1.3, 1.6, 1.5])
            header[0].caption("Field")
            header[1].caption("Value")
            header[2].caption("Printed text")

            with st.form(f"paper-{document.id}"):
                st.markdown(group_title("Copied from the page"), unsafe_allow_html=True)
                correction_inputs: dict[str, tuple[str, str]] = {}
                for key in shown_keys(document):
                    field = document.fields[key]
                    label, value_col, printed = st.columns([1.3, 1.6, 1.5])
                    label.markdown(
                        field_label(field_name(document.document_type, key), field.status == "review"),
                        unsafe_allow_html=True,
                    )
                    current_display = _display(document, key)
                    new_value = value_col.text_input(
                        field_name(document.document_type, key),
                        value=current_display,
                        key=f"value-{document.id}-{key}",
                        label_visibility="collapsed",
                    )
                    printed.markdown(plain(field.raw_text), unsafe_allow_html=True)
                    correction_inputs[key] = (current_display, new_value)

                line_typed: dict[str, str] = {}
                if document.lines:
                    st.write("")
                    st.caption("Lines copied from the page")
                    for index, line in enumerate(document.lines, start=1):
                        description = line.fields.get("description")
                        amount = line.fields.get("amount")
                        description_text = "" if description is None else str(shown_value(description) or "")
                        amount_text = "" if amount is None else str(shown_value(amount) or "")
                        line_label = f"{index}. {description_text} {amount_text}".strip()
                        if document.document_type == "broker_invoice":
                            line_left, line_tax, line_reason = st.columns([2.2, 1.15, 1.15])
                            line_left.markdown(plain(line_label, "body"), unsafe_allow_html=True)
                            for lk, ll in LINE_MANUAL:
                                store_key = f"{document.id}:line:{index}:{lk}"
                                target = line_tax if lk == "tax_code" else line_reason
                                line_typed[store_key] = target.text_input(
                                    ll, value=dossier.manual.get(store_key, ""), key=f"line-{store_key}"
                                )
                        else:
                            st.markdown(plain(line_label, "body"), unsafe_allow_html=True)

                st.write("")
                st.markdown(group_title("You type"), unsafe_allow_html=True)
                st.caption("Not on the PDF. Leave a box empty if you do not have it yet.")
                if document.document_type == "customs_liquidation":
                    st.caption("Payment number above is the liquidation number. SAP reference stays empty until you type it.")
                if document.document_type == "broker_invoice":
                    st.caption("Each service line above has its own Tax code and Reason code.")
                paper_typed: dict[str, str] = {}
                manual_cols = st.columns(2)
                for index, (key, label) in enumerate(_paper_manual_fields(document.document_type)):
                    store_key = f"{document.id}:{key}"
                    paper_typed[store_key] = manual_cols[index % 2].text_input(
                        label, value=dossier.manual.get(store_key, ""), key=f"paper-{store_key}"
                    )

                submitted = st.form_submit_button("Save", type="primary")
                if submitted:
                    set_manual(dossier.id, {**file_typed, **paper_typed, **line_typed})
                    for field_key, (before, after) in correction_inputs.items():
                        if after != before:
                            correct_field(dossier.id, document.id, field_key, after)
                    st.rerun()

        relevant = [item for item in failed if not item.fields or document.id in item.fields]
        for item in relevant:
            tier = "crit" if item.severity == "error" else "warn"
            st.markdown(banner(tier, _check_sentence(dossier, item)), unsafe_allow_html=True)
        if st.session_state["show_passed"]:
            for item in dossier.validation:
                if item.status == "passed" and (not item.fields or document.id in item.fields):
                    st.caption(_check_sentence(dossier, item))

        position = next(index for index, item in enumerate(dossier.documents) if item.id == document.id)
        if position > 0 and st.button("Join with the paper above", key=f"join-{document.id}"):
            merge_document(dossier.id, document.id)
            st.rerun()
        if len(document.page_numbers) > 1:
            after = st.selectbox(
                "Split after",
                document.page_numbers[:-1],
                format_func=lambda page: f"Page {page}",
                key=f"split-after-{document.id}",
            )
            if st.button("Split after this page", key=f"split-{document.id}"):
                split_document(dossier.id, document.id, int(after))
                st.rerun()
