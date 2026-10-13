"""The look of the screen, as three plain CSS files.

tokens.css      colours, radii, shadows (the only place for them)
streamlit.css   overrides of Streamlit's own widgets
components.css  styles for the HTML built in app/ui/components

The files are read on every run, so a CSS edit shows up on the next page refresh.
"""

from pathlib import Path

import streamlit as st

_FOLDER = Path(__file__).parent
# Order matters: tokens first, widget overrides next, component styles last.
_FILES = ("tokens.css", "streamlit.css", "components.css")


def stylesheet() -> str:
    """All three files as one <style> element."""
    css = "\n".join((_FOLDER / name).read_text(encoding="utf-8") for name in _FILES)
    return f"<style>\n{css}\n</style>"


def inject() -> None:
    """Put the stylesheet on the page. Call once, right after set_page_config."""
    st.markdown(stylesheet(), unsafe_allow_html=True)
