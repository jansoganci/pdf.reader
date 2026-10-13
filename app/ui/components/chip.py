from app.ui.components.text import esc

# One word per tier. The same words are used on a row, in the header, and in banners.
TIER_WORDS = {
    "good": "Ready to download",
    "warn": "Needs a check",
    "crit": "Blocks download",
}


def chip(tier: str) -> str:
    """A filled label with the tier's word: on a row or card, and once in the header for the dossier."""
    return f'<span class="chip {tier}">{esc(TIER_WORDS[tier])}</span>'
