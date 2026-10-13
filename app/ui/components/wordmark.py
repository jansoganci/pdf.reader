from app.ui.components.chip import status_pill
from app.ui.components.text import esc


def wordmark(filename: str, paper_count: int, tier: str) -> str:
    """The header block: product name, file name, paper count, dossier state."""
    return (
        f'<div style="display:flex;align-items:center;gap:14px;">'
        f'<div class="brand-mark-inline">📄</div>'
        f'<div><strong style="font-size:20px;">Import file</strong>'
        f'<div style="display:flex;align-items:center;gap:8px;margin-top:3px;">'
        f'<span style="font-size:13px;color:var(--ink-secondary);">{esc(filename)} · {int(paper_count)} papers read</span>'
        f"{status_pill(tier)}"
        f"</div></div></div>"
    )
