from pathlib import Path

FONTS = Path(__file__).resolve().parents[2] / "app" / "ui" / "static" / "fonts"

EXPECTED = [
    f"ibm-plex-{family}-{subset}-{weight}-normal.woff2"
    for family, weights in (("sans", (400, 500, 600)), ("mono", (400, 500)))
    for subset in ("latin", "latin-ext")
    for weight in weights
]


def test_every_font_file_is_present_and_is_woff2():
    for name in EXPECTED:
        data = (FONTS / name).read_bytes()
        assert data[:4] == b"wOF2", name


def test_the_font_license_ships_with_the_fonts():
    assert "SIL Open Font License" in (FONTS / "LICENSE.txt").read_text()
