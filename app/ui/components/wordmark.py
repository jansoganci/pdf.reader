from app.ui.components.chip import chip
from app.ui.components.text import esc


def wordmark(filename: str, paper_count: int, tier: str) -> str:
    """The header block: product name in type, then file name, paper count and dossier state."""
    return (
        '<div class="wordmark">'
        '<div class="wordmark-name">Import file</div>'
        f'<div class="wordmark-meta"><span>{esc(filename)} · {int(paper_count)} papers read</span>{chip(tier)}</div>'
        "</div>"
    )
