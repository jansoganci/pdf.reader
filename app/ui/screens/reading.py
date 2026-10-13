import streamlit as st

from app.pdf.render import PdfRejected
from app.service import process_upload
from app.ui import state
from app.ui.components import banner, plain
from app.ui.lang import t
from app.ui.words import rejection_text


def render(pending: dict) -> None:
    """Read the waiting PDF, then open the result. On failure show the reason and a way back."""
    st.header(t("reading.heading"))
    st.markdown(plain(t("reading.name", name=pending["name"]), "body"), unsafe_allow_html=True)
    st.write(t("reading.wait"))
    with st.status(t("reading.sending"), expanded=True) as status:
        try:
            dossier = process_upload(pending["data"], pending["name"], use_cache=False)
        except PdfRejected as exc:
            _fail(rejection_text(exc.message))
        except RuntimeError as exc:
            _fail(str(exc))
        status.update(label=t("reading.done"), state="complete")
    state.clear_pending()
    state.open_dossier(dossier.id)
    st.rerun()


def _fail(message: str) -> None:
    state.clear_pending()
    st.markdown(banner("crit", message), unsafe_allow_html=True)
    if st.button(t("reading.back")):
        state.go_home()
    st.stop()
