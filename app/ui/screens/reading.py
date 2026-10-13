import streamlit as st

from app.pdf.render import PdfRejected
from app.service import process_upload
from app.ui import state
from app.ui.components import plain


def render(pending: dict) -> None:
    """Read the waiting PDF, then open the result. On failure show the reason and a way back."""
    st.header("Reading the PDF")
    st.markdown(plain(f"{pending['name']} is being read now.", "body"), unsafe_allow_html=True)
    st.write("Please wait. This takes about a minute. Do not close this page.")
    with st.status("Sending the PDF to be read…", expanded=True) as status:
        try:
            dossier = process_upload(pending["data"], pending["name"], use_cache=False)
        except PdfRejected as exc:
            _fail(exc.message)
        except RuntimeError as exc:
            _fail(str(exc))
        status.update(label="Reading finished", state="complete")
    state.clear_pending()
    state.open_dossier(dossier.id)
    st.rerun()


def _fail(message: str) -> None:
    state.clear_pending()
    st.error(message)
    if st.button("Back"):
        state.go_home()
    st.stop()
