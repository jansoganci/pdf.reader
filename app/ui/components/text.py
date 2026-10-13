"""The one escaping path for text that came from a PDF.

Anything read from a PDF is data (AGENTS.md, "Untrusted documents"). It reaches
the screen only as escaped HTML, never as markdown: Streamlit's markdown turns
`[x](url)` into links, `![x](url)` into images that load from outside, and even a
bare `http://...` into a link.

So there are two shapes, and both go through `esc`:

- inside a builder in this package (`banner`, `summary_card`, ...), which escapes
  its own arguments;
- `plain(text)` for a line of PDF text that stands alone, rendered with
  `st.markdown(..., unsafe_allow_html=True)`. A block that starts with a tag is
  not parsed as markdown, so nothing in `text` can become a link or an image.
"""

import html

PLAIN_KINDS = ("caption", "body", "printed", "note")
# printed: what the paper said, in the mono face. note: something the app says, in the sans face.


def esc(value) -> str:
    """Make text safe to put inside HTML. Leaves no markup behind."""
    return html.escape("" if value is None else str(value), quote=True)


def plain(value, kind: str = "caption") -> str:
    """One line of text as an escaped block. `kind` picks the look: caption, body, printed or note."""
    if kind not in PLAIN_KINDS:
        raise ValueError(f"unknown kind: {kind}")
    return f'<div class="pdf-{kind}">{esc(value)}</div>'
