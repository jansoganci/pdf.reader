from app.ui.components.icons import BANNER_ICONS
from app.ui.components.text import esc


def banner(tier: str, text: str) -> str:
    """One sentence in a coloured bar. `text` is plain text; it is escaped here."""
    return f'<div class="banner {tier}">{BANNER_ICONS[tier]}<span>{esc(text)}</span></div>'
