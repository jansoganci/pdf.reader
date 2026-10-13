"""Entry point: language, page setup, the theme, and which screen to show."""

import streamlit as st

from app.ui import lang, state, widgets
from app.ui.screens import reading, review, start
from app.ui.theme import inject

lang.use(state.language())
st.set_page_config(page_title=lang.t("app.title"), layout="wide", initial_sidebar_state="collapsed")
inject()
state.init()
widgets.language_switch()

if state.pending():
    reading.render(state.pending())
elif state.dossier_id():
    review.render(state.dossier_id())
else:
    start.render()
