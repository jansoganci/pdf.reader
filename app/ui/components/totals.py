from app.ui.components.chip import tag
from app.ui.components.text import esc


def summary_card(label: str, amount: str, sub: str, needs_check: bool) -> str:
    """One headline figure. Every argument is plain text and is escaped here."""
    chip = tag("warn") if needs_check else ""
    return (
        f'<div class="card">'
        f'<div class="card-label">{esc(label)}</div>'
        f'<div class="card-amount">{esc(amount)}</div>'
        f'<div class="card-sub">{esc(sub)}</div>{chip}'
        f"</div>"
    )
