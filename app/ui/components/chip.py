from app.ui.components.text import esc

# One word per tier. The same words are used on a row, in the header, and in banners.
TIER_WORDS = {
    "good": "Ready to download",
    "warn": "Needs a check",
    "crit": "Blocks download",
}


def tag(tier: str) -> str:
    """The small label on a row or a card."""
    return f'<span class="tag {tier}">{esc(TIER_WORDS[tier])}</span>'


def status_pill(tier: str) -> str:
    """The dossier state shown once, in the header."""
    return f'<span class="status-pill {tier}">{esc(TIER_WORDS[tier])}</span>'
