"""Everything the screen keeps in `st.session_state`, and every widget key.

One place, so a key is spelled once. The widget keys are the same strings the screen
used before this module existed: Streamlit ties a typed-but-unsaved value to its key,
so renaming a key would silently drop what a person typed when they switch papers.
"""

import streamlit as st

ALLOW_EXPORT_KEY = "allow-export-with-errors"


def init() -> None:
    if "show_passed" not in st.session_state:
        st.session_state["show_passed"] = False


# -- which screen ----------------------------------------------------------------

def pending() -> dict | None:
    """A PDF waiting to be read: {"name", "data"}."""
    return st.session_state.get("pending")


def set_pending(name: str, data: bytes) -> None:
    st.session_state["pending"] = {"name": name, "data": data}


def clear_pending() -> None:
    st.session_state.pop("pending", None)


def dossier_id() -> str | None:
    return st.session_state.get("dossier_id")


def open_dossier(dossier_id: str) -> None:
    st.session_state["dossier_id"] = dossier_id


def close_dossier() -> None:
    st.session_state.pop("dossier_id", None)


def go_home() -> None:
    """Back to the start screen: forget the open dossier and run again."""
    close_dossier()
    st.rerun()


# -- "show passed checks" --------------------------------------------------------

def show_passed() -> bool:
    return bool(st.session_state["show_passed"])


def toggle_show_passed() -> None:
    st.session_state["show_passed"] = not st.session_state["show_passed"]


# -- which page of a paper is open -----------------------------------------------

def page_key(document_id: str) -> str:
    return f"page-{document_id}"


def current_page(document_id: str, default: int | None, pages) -> int | None:
    """The remembered page if it still belongs to the paper, else the default."""
    page = st.session_state.get(page_key(document_id), default)
    return page if page in pages else default


def set_page(document_id: str, page: int) -> None:
    st.session_state[page_key(document_id)] = page


# -- widget keys -----------------------------------------------------------------

def file_key(key: str) -> str:
    return f"file-{key}"


def value_key(document_id: str, key: str) -> str:
    return f"value-{document_id}-{key}"


def paper_key(store_key: str) -> str:
    return f"paper-{store_key}"


def line_key(store_key: str) -> str:
    return f"line-{store_key}"


def form_key(document_id: str) -> str:
    return f"paper-{document_id}"


def prev_key(document_id: str) -> str:
    return f"prev-{document_id}"


def next_key(document_id: str) -> str:
    return f"next-{document_id}"


def join_key(document_id: str) -> str:
    return f"join-{document_id}"


def split_after_key(document_id: str) -> str:
    return f"split-after-{document_id}"


def split_key(document_id: str) -> str:
    return f"split-{document_id}"
