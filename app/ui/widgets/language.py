import streamlit as st

from app.ui import state
from app.ui.lang import LANGUAGES, SWITCH_LABELS

# Fixed on purpose: a label that changes with the language would change the widget's identity on every
# switch, and Streamlit would reset it (the same trap as a changing `value`, see state.init_override).
LABEL = "Langue / Language"


def language_switch() -> None:
    """A small FR / EN switch at the top right of every screen. The first language in `LANGUAGES`
    is the default, so no `index` is passed and the choice lives only under `state.LANGUAGE_KEY`.
    Nothing about the widget (label, options, their words) may depend on the language."""
    _, right = st.columns([9, 1])
    right.radio(
        LABEL,
        LANGUAGES,
        format_func=SWITCH_LABELS.get,
        horizontal=True,
        key=state.LANGUAGE_KEY,
        label_visibility="collapsed",
    )
