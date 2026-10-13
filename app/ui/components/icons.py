"""Inline status icons: 16x16, stroke, `currentColor`. See docs/design.md section 5.5."""

_ATTRS = (
    'width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" '
    'stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"'
)

BANNER_ICONS = {
    "good": f'<svg {_ATTRS}><circle cx="8" cy="8" r="6.25"/><path d="M5.3 8.2l1.8 1.8 3.6-3.8"/></svg>',
    "warn": (
        f'<svg {_ATTRS}><path d="M8 2.2l6.3 11A1 1 0 0 1 13.4 15H2.6a1 1 0 0 1-.9-1.8z"/>'
        '<path d="M8 6.3v3"/><circle cx="8" cy="11.4" r="0.7" fill="currentColor" stroke="none"/></svg>'
    ),
    "crit": f'<svg {_ATTRS}><circle cx="8" cy="8" r="6.25"/><path d="M5.8 5.8l4.4 4.4M10.2 5.8l-4.4 4.4"/></svg>',
}
