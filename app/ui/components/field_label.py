from app.ui.components.chip import chip
from app.ui.components.text import esc


def field_label(text: str, needs_check: bool = False) -> str:
    """A row label, with the chip after it when the value needs a check."""
    return f"{esc(text)} {chip('warn')}" if needs_check else esc(text)


def group_title(text: str) -> str:
    return f'<div class="group-title">{esc(text)}</div>'
