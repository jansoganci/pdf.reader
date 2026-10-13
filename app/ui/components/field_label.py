from app.ui.components.chip import chip, edited_mark
from app.ui.components.text import esc


def field_label(text: str, needs_check: bool = False, edited: bool = False) -> str:
    """A row label, then the chip when the value needs a check, then the mark when a person changed it."""
    parts = [esc(text)]
    if needs_check:
        parts.append(chip("warn"))
    if edited:
        parts.append(edited_mark())
    return " ".join(parts)


def group_title(text: str) -> str:
    return f'<div class="group-title">{esc(text)}</div>'
