import streamlit as st

from app.pdf.render import PdfRejected
from app.service import (
    correct_field,
    export_dossier,
    get_dossier,
    list_dossiers,
    mark_export_with_errors,
    process_upload,
)

st.set_page_config(page_title="Import dossier reader", layout="wide")
st.title("Import dossier reader")
st.caption("Reads a scanned import file, checks the numbers, and exports JSON or CSV. It does not post to SAP.")

uploaded = st.file_uploader("Upload one PDF", type=["pdf"])
if uploaded is not None and st.button("Read dossier"):
    try:
        dossier = process_upload(uploaded.getvalue(), uploaded.name)
        st.session_state["dossier_id"] = dossier.id
        st.success(f"Dossier {dossier.id} is {dossier.status}.")
    except PdfRejected as exc:
        st.error(exc.message)
    except RuntimeError as exc:
        st.error(str(exc))

st.subheader("Saved dossiers")
rows = list_dossiers()
if not rows:
    st.info("No dossiers yet.")
else:
    labels = {f"{row['filename']} ({row['status']})": row["id"] for row in rows}
    choice = st.selectbox("Open", list(labels))
    st.session_state["dossier_id"] = labels[choice]

dossier_id = st.session_state.get("dossier_id")
if not dossier_id:
    st.stop()

dossier = get_dossier(dossier_id)
if dossier is None:
    st.stop()

st.write(f"Estimated cost: ${dossier.estimated_cost_usd:.4f}")
left, right = st.columns(2)
with left:
    st.subheader("Documents")
    for document in dossier.documents:
        st.markdown(f"**{document.document_type}** pages {document.page_numbers}")
        if document.review_reason:
            st.warning(document.review_reason)
        for name, field in document.fields.items():
            if field.status == "missing" and field.value is None and field.raw_text is None:
                continue
            shown = field.user_value if field.user_value is not None else field.value
            st.text(f"{name}: {shown} [{field.status}] raw={field.raw_text} page={field.source_page}")
            if field.user_value is not None:
                st.caption(f"Extracted value: {field.value}")
with right:
    st.subheader("Checks")
    for item in dossier.validation:
        line = f"{item.rule_id}: {item.status} — {item.message}"
        if item.status == "failed":
            st.error(line)
        else:
            st.write(line)

st.subheader("Correct a field")
document_ids = [item.id for item in dossier.documents]
selected = st.selectbox("Document", document_ids)
document = next(item for item in dossier.documents if item.id == selected)
field_name = st.selectbox("Field", list(document.fields))
new_value = st.text_input("Corrected value")
if st.button("Save correction") and new_value != "":
    correct_field(dossier.id, selected, field_name, new_value)
    st.rerun()

errors = [item for item in dossier.validation if item.status == "failed" and item.severity == "error"]
if errors:
    allowed = st.checkbox("Export even though checks failed", value=dossier.export_with_errors)
    if allowed != dossier.export_with_errors:
        mark_export_with_errors(dossier.id, allowed)
        st.rerun()

if st.button("Export JSON and CSV"):
    try:
        export_dossier(dossier.id, "json")
        export_dossier(dossier.id, "fields_csv")
        export_dossier(dossier.id, "lines_csv")
        st.success("Export saved in the local data folder.")
    except PermissionError as exc:
        st.error(str(exc))
