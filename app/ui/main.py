"""Entry point: page setup, the theme, and which screen to show."""

import streamlit as st

from app.ui import state
from app.ui.screens import reading, review, start
from app.ui.theme import inject

st.set_page_config(page_title="Import file", layout="wide", initial_sidebar_state="collapsed")
inject()
state.init()

if state.pending():
    reading.render(state.pending())
elif state.dossier_id():
    review.render(state.dossier_id())
else:
    start.render()
