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
    split_document,
)
from app.ui.words import check_sentence, field_name, file_status, issued_by, money_text, pages_text, paper_name, shown_value

st.set_page_config(page_title="Import file", layout="wide", initial_sidebar_state="collapsed")
st.markdown(
    """
    <style>
    header, [data-testid="stHeader"], [data-testid="stToolbar"],
    [data-testid="stDecoration"], #MainMenu, footer { display: none !important; }
    [data-testid="stHeaderActionElements"], [data-testid="stHeadingWithActionElements"] a { display: none !important; }
    .stApp { background: #f4f1ea; }
    .block-container { padding: 1.25rem 2rem 3rem; max-width: 1240px; }
    button { white-space: nowrap !important; }
    div[data-testid="stCaptionContainer"] { color: #6b645b; }
    .banner { border-radius: 12px; padding: 12px 16px; font-family: "Segoe UI", sans-serif; margin: 8px 0 16px; }
    .banner.warn { background: #f8ecd8; color: #8a5a12; }
    .banner.ok { background: #e5f4eb; color: #1f6b45; }
    .tag { display: inline-block; background: #f8ecd8; color: #8a5a12; border-radius: 999px;
           padding: 2px 8px; font-size: 12px; font-family: "Segoe UI", sans-serif; }
    </style>
    """,
    unsafe_allow_html=True,
)

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


def _visible_fields(document: DocumentRecord) -> list[str]:
    names = []
    for key, field in document.fields.items():
        if shown_value(field) in (None, "") and not field.raw_text and field.status != "review":
            continue
        names.append(key)
    return names


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


def _selected_document(dossier: Dossier) -> DocumentRecord:
    chosen = st.session_state.get("paper_id")
    if chosen and any(item.id == chosen for item in dossier.documents):
        return next(item for item in dossier.documents if item.id == chosen)
    return dossier.documents[0]


def _start_home() -> None:
    st.session_state.pop("dossier_id", None)
    st.session_state.pop("paper_id", None)
    st.session_state.pop("pending", None)
    st.rerun()


if "show_passed" not in st.session_state:
    st.session_state["show_passed"] = False

pending = st.session_state.get("pending")
if pending:
    st.header("Reading the PDF")
    st.write(f"{pending['name']} is being read now.")
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
    st.session_state["paper_id"] = dossier.documents[0].id if dossier.documents else None
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

head_left, head_right = st.columns([2, 3])
with head_left:
    st.header("Import file")
    st.caption(f"{dossier.filename} · {file_status(dossier.status)}")
with head_right:
    actions = st.columns([1.3, 1, 1, 1.4])
    if actions[0].button("Read another file"):
        _start_home()
    if blocking and not dossier.export_with_errors:
        allow = actions[3].checkbox("Download anyway")
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
            actions[1].download_button("Download CSV", csv_path.read_bytes(), file_name="fields.csv")
            actions[2].download_button("Download JSON", json_path.read_bytes(), file_name="import-file.json", type="primary")

if failed:
    st.markdown(f'<div class="banner warn">{len(failed)} items need a check before you download.</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="banner ok">Ready to download.</div>', unsafe_allow_html=True)
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
        with column:
            st.markdown(f"**{label}**")
            st.markdown(f"## {amount}")
            who = issued_by(found)
            if kind == "customs_declaration":
                st.caption("Copied from the customs papers")
            elif who:
                st.caption(f"Issued by {who}")
            if needs:
                st.markdown('<span class="tag">Needs a check</span>', unsafe_allow_html=True)

st.write("")
list_column, detail_column = st.columns([1, 2.3], gap="large")
with list_column:
    for item in dossier.documents:
        amount = _headline_amount(item)
        who = issued_by(item)
        bits = [pages_text(item.page_numbers)]
        if who:
            bits.append(f"Issued by {who}")
        if amount:
            bits.append(amount)
        selected = item.id == st.session_state.get("paper_id", dossier.documents[0].id)
        if st.button(
            paper_name(item.document_type),
            key=f"open-{item.id}",
            width="stretch",
            type="primary" if selected else "secondary",
        ):
            st.session_state["paper_id"] = item.id
            st.rerun()
        st.caption(" · ".join(bits))

document = _selected_document(dossier)
with detail_column:
    st.subheader(paper_name(document.document_type))
    who = issued_by(document)
    st.caption(" · ".join(bit for bit in (pages_text(document.page_numbers), f"Issued by {who}" if who else "") if bit))
    preview, fields = st.columns([1.15, 1.6], gap="large")
    with preview:
        if document.page_numbers:
            image = page_image(dossier.id, document.page_numbers[0])
            if image:
                st.image(image, width="stretch")
            extra = document.page_numbers[1:]
            if extra:
                st.caption("Also " + ", ".join(f"page {page}" for page in extra) + " of this same paper.")
    with fields:
        header = st.columns([1.3, 1.5, 1.5, 0.9])
        header[0].caption("Field")
        header[1].caption("Value")
        header[2].caption("Printed text")
        for key in _visible_fields(document):
            field = document.fields[key]
            label, value, printed, action = st.columns([1.3, 1.5, 1.5, 0.9])
            label.write(field_name(document.document_type, key))
            value.write(_display(document, key) or " ")
            if field.status == "review":
                value.markdown('<span class="tag">Needs a check</span>', unsafe_allow_html=True)
            printed.caption(field.raw_text or "")
            if action.button("Correct", key=f"edit-{document.id}-{key}"):
                st.session_state["editing"] = (document.id, key)
        editing = st.session_state.get("editing")
        if editing and editing[0] == document.id:
            new_value = st.text_input(field_name(document.document_type, editing[1]))
            if st.button("Save correction", type="primary") and new_value != "":
                correct_field(dossier.id, document.id, editing[1], new_value)
                st.session_state["editing"] = None
                st.rerun()

    relevant = [item for item in failed if not item.fields or document.id in item.fields]
    for item in relevant:
        st.markdown(f'<div class="banner warn">{_check_sentence(dossier, item)}</div>', unsafe_allow_html=True)
    if st.session_state["show_passed"]:
        for item in dossier.validation:
            if item.status == "passed" and (not item.fields or document.id in item.fields):
                st.caption(_check_sentence(dossier, item))

    position = next(index for index, item in enumerate(dossier.documents) if item.id == document.id)
    if position > 0 and st.button("Join with the paper above"):
        merge_document(dossier.id, document.id)
        st.session_state["paper_id"] = dossier.documents[position - 1].id
        st.rerun()
    if len(document.page_numbers) > 1:
        after = st.selectbox("Split after", document.page_numbers[:-1], format_func=lambda page: f"Page {page}")
        if st.button("Split after this page"):
            split_document(dossier.id, document.id, int(after))
            st.rerun()
