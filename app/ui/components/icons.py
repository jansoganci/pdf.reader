"""Status glyphs for the badge: 16x16, stroke, `currentColor`. See docs/design.md section 5.5.

Three meanings only: a tick (good), an exclamation mark (needs a check), a cross (blocks).
The badge, not the glyph, carries the colour.
"""

_ATTRS = 'viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"'

GLYPHS = {
    "good": f'<svg {_ATTRS}><path d="M3.8 8.4l2.7 2.7 5.7-6"/></svg>',
    "warn": f'<svg {_ATTRS}><path d="M8 3.5v5.2"/><circle cx="8" cy="12" r="0.4" fill="currentColor"/></svg>',
    "crit": f'<svg {_ATTRS}><path d="M4.5 4.5l7 7M11.5 4.5l-7 7"/></svg>',
}
