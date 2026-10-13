"""docs/design.md as tests: the banned habits (section 5.1) and the contrast table (section 8).

These read the CSS files in app/ui/theme and fail when a banned pattern comes back, so the
look cannot drift back to a generated default without someone noticing.
"""

import re
from pathlib import Path

import pytest

from app.config import settings

ROOT = Path(__file__).resolve().parents[2]
THEME = ROOT / "app" / "ui" / "theme"
CSS_FILES = ("fonts.css", "tokens.css", "streamlit.css", "components.css")


def _css(name: str) -> str:
    text = (THEME / name).read_text()
    return re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)  # comments may name what is banned


ALL_CSS = "\n".join(_css(name) for name in CSS_FILES)


# -- section 5.1: what this must not look like ---------------------------------------

def test_no_coloured_bar_on_one_side_of_a_box():
    assert not re.search(r"border-(left|right|top|bottom)\s*:\s*[2-9]\d*px", ALL_CSS)
    assert "border-left-color" not in ALL_CSS


def test_nothing_is_lifted_with_a_shadow():
    assert not re.search(r"box-shadow\s*:(?!\s*none)", ALL_CSS)
    assert "drop-shadow" not in ALL_CSS and "text-shadow" not in ALL_CSS
    assert "--shadow" not in ALL_CSS


def test_radii_are_small_and_nothing_is_a_pill_or_a_circle():
    for value in re.findall(r"border-radius\s*:\s*([^;}]+)", ALL_CSS):
        value = value.replace("!important", "").strip()
        assert value == "0" or re.fullmatch(r"var\(--radius-(sm|md|lg)\)", value), value
    for name, px in re.findall(r"--(radius-[a-z]+)\s*:\s*(\d+)px", ALL_CSS):
        assert int(px) <= 6, name


def test_no_gradients_glass_or_glow():
    for banned in ("gradient(", "backdrop-filter", "filter: blur", "blur("):
        assert banned not in ALL_CSS, banned


def test_the_generated_default_font_and_outside_font_hosts_are_gone():
    assert not re.search(r"\bInter\b", ALL_CSS)
    assert "googleapis" not in ALL_CSS and "gstatic" not in ALL_CSS and "@import" not in ALL_CSS
    assert "IBM Plex Sans" in ALL_CSS and "IBM Plex Mono" in ALL_CSS


def test_the_generated_default_colours_are_gone():
    banned = {
        # indigo / violet accents
        "#4f46e5", "#4338ca", "#a5b4fc", "#1e1b4b", "#eef2ff", "#6366f1",
        # zinc neutrals
        "#fafafa", "#f4f4f5", "#e4e4e7", "#18181b", "#52525b", "#a1a1aa", "#71717a", "#0f0f12", "#2a2a2e",
        # pastel status tints
        "#dcfce7", "#fef3c7", "#fee2e2", "#14281d", "#2b2111", "#2c1515",
    }
    found = {value.lower() for value in re.findall(r"#[0-9a-fA-F]{3,8}\b", ALL_CSS)}
    assert not (found & banned), sorted(found & banned)


def test_colours_are_written_only_in_the_tokens_file():
    for name in ("fonts.css", "streamlit.css", "components.css"):
        assert not re.search(r"#[0-9a-fA-F]{3,8}\b", _css(name)), name
        assert not re.search(r"\brgba?\(|\bhsla?\(", _css(name)), name


def test_no_emoji_in_the_screen_code():
    emoji = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
    for path in (ROOT / "app" / "ui").rglob("*.py"):
        assert not emoji.search(path.read_text()), path.name


# -- section 9: the fonts and the upload limit ---------------------------------------

def test_every_font_file_the_css_names_is_in_the_repo():
    names = re.findall(r"/app/static/fonts/([\w.-]+\.woff2)", ALL_CSS)
    assert len(names) == 10  # sans x3 weights and mono x2 weights, each in Latin and Latin Extended
    for name in names:
        assert (ROOT / "app" / "ui" / "static" / "fonts" / name).is_file(), name


def test_the_run_command_serves_fonts_and_states_the_upload_limit():
    readme = (ROOT / "README.md").read_text()
    assert "--server.enableStaticServing true" in readme
    assert f"--server.maxUploadSize {settings.max_upload_bytes // (1024 * 1024)}" in readme


# -- section 8: contrast, computed from the tokens -----------------------------------

def _tokens(block_start: str) -> dict[str, str]:
    text = (THEME / "tokens.css").read_text()
    start = text.index(block_start)
    body = text[text.index("{", start) + 1 : text.index("\n}", start)]
    return dict(re.findall(r"--([a-z-]+)\s*:\s*(#[0-9a-fA-F]{6})", body))


def _luminance(hex_colour: str) -> float:
    channels = [int(hex_colour[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(a: str, b: str) -> float:
    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


LIGHT = _tokens(":root {")
DARK = _tokens(':root[data-theme="dark"]')

# (foreground, background, floor): 4.5 for text, 3 for control borders and focus rings.
PAIRS = [
    ("ink", "surface", 4.5), ("ink", "bg", 4.5), ("ink", "surface-sunken", 4.5),
    ("ink-secondary", "surface", 4.5), ("ink-secondary", "bg", 4.5), ("ink-secondary", "surface-sunken", 4.5),
    ("on-accent", "accent", 4.5), ("on-accent", "accent-hover", 4.5),
    ("accent-text", "surface", 4.5), ("accent-text", "bg", 4.5),
    ("on-review", "review-fill", 4.5), ("on-crit", "crit-fill", 4.5), ("on-good", "good-fill", 4.5),
    ("review-text", "surface", 4.5), ("crit-text", "surface", 4.5), ("good-text", "surface", 4.5),
    ("edge", "surface", 3.0), ("edge", "bg", 3.0), ("accent-text", "surface", 3.0),
]


@pytest.mark.parametrize("theme,tokens", [("light", LIGHT), ("dark", DARK)])
def test_contrast_floors_hold_in_both_themes(theme, tokens):
    failures = [
        f"{fg} on {bg}: {_contrast(tokens[fg], tokens[bg]):.2f} < {floor}"
        for fg, bg, floor in PAIRS
        if _contrast(tokens[fg], tokens[bg]) < floor
    ]
    assert not failures, f"{theme}: {failures}"


def test_both_themes_define_the_same_tokens():
    assert set(LIGHT) == set(DARK)
