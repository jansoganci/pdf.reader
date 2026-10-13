from app.ui.components.text import esc
from app.ui.lang import t


def tier_word(tier: str) -> str:
    """One word per tier. The same words are used on a row, in the header, and in banners."""
    return t(f"tier.{tier}")


def chip(tier: str) -> str:
    """A filled label with the tier's word: on a row or card, and once in the header for the dossier."""
    return f'<span class="chip {tier}">{esc(tier_word(tier))}</span>'


def edited_mark() -> str:
    """A small outlined label for a value a person changed. Outlined, not filled: it is information,
    not a status, so it never competes with the chips."""
    return f'<span class="mark">{esc(t("edited"))}</span>'
