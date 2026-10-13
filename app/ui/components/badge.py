from app.ui.components.icons import GLYPHS


def badge(tier: str) -> str:
    """The square with a glyph at the start of a banner. The tier picks the fill."""
    return f'<span class="badge {tier}">{GLYPHS[tier]}</span>'
