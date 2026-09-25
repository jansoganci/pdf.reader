import streamlit as st

from app.models import DocumentRecord, Dossier
from app.pdf.render import PdfRejected
from app.service import (
    correct_field,
    export_dossier,
    get_dossier,
    list_dossiers,
    mark_export_with_errors,
    merge_document,
    page_image,
    process_upload,
    split_document,
)
from app.ui.words import check_sentence, field_name, file_status, issued_by, money_text, pages_text, paper_name, shown_value

st.set_page_config(page_title="Import file", layout="wide")
st.markdown(
    """
    <style>
    .block-container { padding-top: 1.4rem; max-width: 1200px; }
    div[data-testid="stCaptionContainer"] { color: #6b645b; }
    </style>
    """,
    unsafe_allow_html=True,
)

MONEY_KEYS = {
    "net_amount",
    "tax_amount",
    "total_amount",
    "fob_amount",
    "freight_amount",
    "customs_value",
    "insurance_amount",
}


def _currency(document: DocumentRecord) -> str | None:
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
    if key in MONEY_KEYS or key == "exchange_rate":
        currency = None if key in {"exchange_rate", "customs_value"} else _currency(document)
        return money_text(value, currency)
    return "" if value in (None, "") else str(value)


def _headline_amount(document: DocumentRecord) -> str:
    for key in ("total_amount", "customs_value"):
        text = _display(document, key)
        if text:
            return text
    return ""


def _visible_fields(document: DocumentRecord) -> list[str]:
    names = []
    for key, field in document.fields.items():
        if shown_value(field) in (None, "") and not field.raw_text:
            continue
        names.append(key)
    return names


def _check_sentence(dossier: Dossier, item) -> str:
    names = []
    for document_id in item.fields:
        document = next((doc for doc in dossier.documents if doc.id == document_id), None)
        if document is not None:
            names.append(paper_name(document.document_type))
    paper = names[0] if len(names) == 1 else None
    if item.status == "passed":
        return f"{paper}: {item.message}" if paper else item.message
    return check_sentence(item.rule_id, item.message, paper)


def _selected_document(dossier: Dossier) -> DocumentRecord:
    chosen = st.session_state.get("paper_id")
    if chosen and any(item.id == chosen for item in dossier.documents):
        return next(item for item in dossier.documents if item.id == chosen)
    return dossier.documents[0]


if "show_passed" not in st.session_state:
    st.session_state["show_passed"] = False

with st.expander("Read another PDF", expanded=not st.session_state.get("dossier_id")):
    uploaded = st.file_uploader("PDF", type=["pdf"], label_visibility="collapsed")
    if uploaded is not None and st.button("Read this PDF", type="primary"):
        with st.spinner("Reading the PDF…"):
            try:
                dossier = process_upload(uploaded.getvalue(), uploaded.name)
            except PdfRejected as exc:
                st.error(exc.message)
            except RuntimeError as exc:
                st.error(str(exc))
            else:
                st.session_state["dossier_id"] = dossier.id
                st.session_state["paper_id"] = dossier.documents[0].id if dossier.documents else None
                st.rerun()

rows = list_dossiers()
if rows:
    labels = {
        f"{row['filename']} · {file_status(row['status'])} · {row['created_at']}": row["id"] for row in rows
    }
    current = st.session_state.get("dossier_id")
    options = list(labels)
    index = 0
    for position, label in enumerate(options):
        if labels[label] == current:
            index = position
    choice = st.selectbox("Open a saved file", options, index=index)
    if labels[choice] != current:
        st.session_state["dossier_id"] = labels[choice]
        st.session_state["paper_id"] = None
        st.rerun()

dossier_id = st.session_state.get("dossier_id")
if not dossier_id:
    st.stop()
dossier = get_dossier(dossier_id)
if dossier is None or not dossier.documents:
    st.info("This file could not be opened.")
    st.stop()

failed = [item for item in dossier.validation if item.status == "failed"]
blocking = [item for item in failed if item.severity == "error"]

title, downloads = st.columns([3, 2])
with title:
    st.header("Import file")
    st.caption(f"{dossier.filename} · {file_status(dossier.status)}")
with downloads:
    if blocking and not dossier.export_with_errors:
        allow = st.checkbox("Download anyway. Some checks still need a look.")
        if allow:
            mark_export_with_errors(dossier.id, True)
            st.rerun()
    try:
        csv_path = export_dossier(dossier.id, "fields_csv")
        json_path = export_dossier(dossier.id, "json")
    except PermissionError:
        csv_path = json_path = None
    one, two = st.columns(2)
    if csv_path and json_path:
        one.download_button("Download CSV", csv_path.read_bytes(), file_name="fields.csv")
        two.download_button("Download JSON", json_path.read_bytes(), file_name="import-file.json")

if failed and not st.session_state["show_passed"]:
    note, toggle = st.columns([4, 1])
    note.warning(f"{len(failed)} items need a check before you rely on the download.")
    if toggle.button("Show passed checks"):
        st.session_state["show_passed"] = True
        st.rerun()
elif st.session_state["show_passed"] and st.button("Hide passed checks"):
    st.session_state["show_passed"] = False
    st.rerun()

summary = []
for kind, label in (
    ("supplier_invoice", "Supplier invoice"),
    ("customs_declaration", "Customs value"),
    ("customs_liquidation", "Customs payment"),
    ("carrier_invoice", "Shipping invoice"),
):
    document = next((item for item in dossier.documents if item.document_type == kind), None)
    if document is None:
        continue
    key = "customs_value" if kind == "customs_declaration" else "total_amount"
    amount = _display(document, key) or "Not read"
    who = issued_by(document)
    summary.append((label, amount, who, any(field.status == "review" for field in document.fields.values())))
if summary:
    cards = st.columns(len(summary))
    for column, (label, amount, who, needs) in zip(cards, summary):
        with column:
            st.metric(label, amount)
            if who and label not in {"Customs value", "Customs payment"}:
                st.caption(f"Issued by {who}")
            elif label == "Customs value":
                st.caption("Copied from the customs papers")
            if needs:
                st.caption("Needs a check")

list_column, detail_column = st.columns([1, 2])
with list_column:
    for document in dossier.documents:
        amount = _headline_amount(document)
        who = issued_by(document)
        bits = [pages_text(document.page_numbers)]
        if who:
            bits.append(f"Issued by {who}")
        if amount:
            bits.append(amount)
        if st.button(
            paper_name(document.document_type),
            key=f"open-{document.id}",
            width="stretch",
        ):
            st.session_state["paper_id"] = document.id
            st.rerun()
        st.caption(" · ".join(bits))

document = _selected_document(dossier)
with detail_column:
    st.subheader(paper_name(document.document_type))
    st.caption(" · ".join(
        bit for bit in (pages_text(document.page_numbers), f"Issued by {issued_by(document)}" if issued_by(document) else "") if bit
    ))
    preview, fields = st.columns([1, 2])
    with preview:
        if document.page_numbers:
            image = page_image(dossier.id, document.page_numbers[0])
            if image:
                st.image(image, width="stretch")
            extra = document.page_numbers[1:]
            if extra:
                st.caption("Also " + ", ".join(f"page {page}" for page in extra) + " of this same paper.")
    with fields:
        for key in _visible_fields(document):
            field = document.fields[key]
            label, value, printed, action = st.columns([1.1, 1.4, 1.4, 0.7])
            label.write(field_name(document.document_type, key))
            text = _display(document, key) or str(shown_value(field) or "")
            value.write(text + ("  · Needs a check" if field.status == "review" else ""))
            printed.caption(field.raw_text or "")
            if action.button("Correct", key=f"edit-{document.id}-{key}"):
                st.session_state["editing"] = (document.id, key)
        editing = st.session_state.get("editing")
        if editing and editing[0] == document.id:
            new_value = st.text_input("Corrected value", key=f"value-{editing[1]}")
            if st.button("Save correction") and new_value != "":
                correct_field(dossier.id, document.id, editing[1], new_value)
                st.session_state["editing"] = None
                st.rerun()
        line_rows = []
        for index, line in enumerate(document.lines, start=1):
            amount = line.fields.get("amount")
            if amount is None or shown_value(amount) in (None, ""):
                continue
            description = line.fields.get("description")
            line_rows.append(
                {
                    "Line": index,
                    "Description": "" if description is None else (shown_value(description) or ""),
                    "Amount": money_text(shown_value(amount), _currency(document)),
                }
            )
        if line_rows:
            st.caption("Lines")
            st.dataframe(line_rows, hide_index=True, width="stretch")

    relevant = [
        item
        for item in dossier.validation
        if item.status == "failed" and (not item.fields or document.id in item.fields)
    ]
    for item in relevant:
        st.warning(_check_sentence(dossier, item))
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
        after = st.selectbox(
            "Split after",
            document.page_numbers[:-1],
            format_func=lambda page: f"Page {page}",
        )
        if st.button("Split after this page"):
            split_document(dossier.id, document.id, int(after))
            st.rerun()
