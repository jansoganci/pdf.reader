import re
from pathlib import Path

from app.ui import theme

UI = Path(__file__).resolve().parents[2] / "app" / "ui"
FILES = ("tokens.css", "streamlit.css", "components.css")


def test_the_stylesheet_is_one_style_element_with_the_three_files_in_order():
    css = theme.stylesheet()
    assert css.startswith("<style>") and css.endswith("</style>")
    assert css.count("<style>") == 1 and css.count("</style>") == 1
    positions = [css.index(marker) for marker in ("--accent:", "stBaseButton-primary", ".banner {")]
    assert positions == sorted(positions)


def test_tokens_define_both_themes():
    tokens = (UI / "theme" / "tokens.css").read_text()
    assert ":root {" in tokens
    assert "prefers-color-scheme: dark" in tokens
    assert ':root[data-theme="dark"]' in tokens


def test_every_css_variable_in_use_is_defined():
    css = theme.stylesheet()
    defined = set(re.findall(r"(--[a-z0-9-]+)\s*:", (UI / "theme" / "tokens.css").read_text()))
    used = set(re.findall(r"var\((--[a-z0-9-]+)\)", css))
    assert used <= defined, sorted(used - defined)


def test_no_css_or_colour_values_live_outside_the_theme_folder():
    for path in UI.glob("*.py"):
        source = path.read_text()
        assert "<style" not in source, path.name
        assert not re.search(r"#[0-9a-fA-F]{6}\b", source), path.name
