from app.ui.components.text import esc
from app.ui.lang import t


def page_label(page_number: int, position: int, total: int) -> str:
    """The text between the page buttons. Only numbers go in, and they are forced to int."""
    text = t("page.label", page=int(page_number), position=int(position) + 1, total=int(total))
    return f'<div style="text-align:center">{esc(text)}</div>'
