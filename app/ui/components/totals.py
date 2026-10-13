from collections.abc import Sequence

from app.ui.components.chip import chip
from app.ui.components.text import esc


def totals_strip(cells: Sequence) -> str:
    """One ruled row of headline figures. Each cell has `label`, `amount`, `sub` and
    `needs_check`; all text is plain and is escaped here."""
    parts = []
    for cell in cells:
        parts.append(
            '<div class="totals-cell">'
            f'<div class="totals-label">{esc(cell.label)}</div>'
            f'<div class="totals-figure">{esc(cell.amount)}</div>'
            f'<div class="totals-sub">{esc(cell.sub)}</div>'
            f'{chip("warn") if cell.needs_check else ""}'
            "</div>"
        )
    return f'<div class="totals">{"".join(parts)}</div>'
