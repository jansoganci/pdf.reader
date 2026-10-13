from app.ui.components.badge import badge
from app.ui.components.text import esc


def banner(tier: str, text: str) -> str:
    """One sentence on paper with a badge. `text` is plain text; it is escaped here.

    The sentence stays in ink; only the badge carries the tier colour. No bar on the side
    and no tinted ground (docs/design.md section 5.1).
    """
    return f'<div class="banner {tier}">{badge(tier)}<span class="banner-text">{esc(text)}</span></div>'
