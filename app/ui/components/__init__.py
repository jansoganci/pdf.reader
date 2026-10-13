"""Pure HTML builders for the screen.

Rules (docs/UI_PLAN.md section 3): nothing here imports `streamlit` or
`app.service`, and every argument is plain text that is escaped inside the
builder. Callers never escape for these functions.
"""

from app.ui.components.banner import banner
from app.ui.components.chip import TIER_WORDS, status_pill, tag
from app.ui.components.field_label import field_label, group_title
from app.ui.components.page_label import page_label
from app.ui.components.text import esc, plain
from app.ui.components.totals import summary_card
from app.ui.components.wordmark import wordmark

__all__ = [
    "TIER_WORDS",
    "banner",
    "esc",
    "field_label",
    "group_title",
    "page_label",
    "plain",
    "status_pill",
    "summary_card",
    "tag",
    "wordmark",
]
