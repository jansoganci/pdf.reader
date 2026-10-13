from app.ui.components.chip import chip
from app.ui.components.text import esc
from app.ui.lang import t, tn


def wordmark(filename: str, paper_count: int, tier: str) -> str:
    """The header block: product name in type, then file name, paper count and dossier state."""
    return (
        '<div class="wordmark">'
        f'<div class="wordmark-name">{esc(t("wordmark.name"))}</div>'
        f'<div class="wordmark-meta"><span>{esc(filename)} · {esc(tn("wordmark.papers", int(paper_count)))}</span>{chip(tier)}</div>'
        "</div>"
    )
