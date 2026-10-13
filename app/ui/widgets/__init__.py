"""Pieces of the screen that call Streamlit (docs/UI_PLAN.md section 3).

A widget draws something and returns what the person did. It never calls the service
and never saves; the screen does that with what the widget returns.
"""

from app.ui.widgets.check_list import check_list
from app.ui.widgets.export import export_row
from app.ui.widgets.header import header
from app.ui.widgets.join_split import JoinSplitAction, join_split
from app.ui.widgets.language import language_switch
from app.ui.widgets.page_viewer import page_viewer
from app.ui.widgets.paper_form import FormResult, paper_form
from app.ui.widgets.strip import strip

__all__ = [
    "FormResult",
    "JoinSplitAction",
    "check_list",
    "export_row",
    "header",
    "join_split",
    "language_switch",
    "page_viewer",
    "paper_form",
    "strip",
]
