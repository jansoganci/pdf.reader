import re
from pathlib import Path

import pytest

from app.ui.components import (
    badge,
    banner,
    chip,
    edited_mark,
    esc,
    field_label,
    group_title,
    page_label,
    plain,
    tier_word,
    totals_strip,
    wordmark,
)

# What a hostile PDF could print where a company name or a line description goes.
HOSTILE = '<img src=x onerror="alert(1)"> <script>x()</script> "q" \'s\' & **b** [l](http://evil.example/)'


def _no_live_markup(html_text: str) -> None:
    assert "<img" not in html_text
    assert "<script" not in html_text
    assert 'onerror="' not in html_text


def test_esc_removes_all_markup():
    out = esc(HOSTILE)
    _no_live_markup(out)
    assert "&lt;img" in out and "&lt;script" in out and "&quot;" in out and "&amp;" in out


def test_esc_handles_none_and_numbers():
    assert esc(None) == ""
    assert esc(12.5) == "12.5"


def test_banner_escapes_its_text_and_keeps_the_tier():
    out = banner("crit", HOSTILE)
    _no_live_markup(out)
    assert out.startswith('<div class="banner crit">')
    assert out.endswith("</span></div>")


@pytest.mark.parametrize("tier", ["good", "warn", "crit"])
def test_every_tier_has_a_glyph_a_badge_and_a_word(tier):
    assert "<svg" in badge(tier)
    assert f'class="badge {tier}"' in banner(tier, "x")
    assert tier_word(tier) in chip(tier)


def test_a_banner_has_no_side_bar_or_tint_hook():
    # Status colour lives in the badge only; the sentence is a plain span.
    out = banner("warn", "x")
    assert out == (
        f'<div class="banner warn">{badge("warn")}<span class="banner-text">x</span></div>'
    )


def test_chip_markup_has_the_word_and_no_dot():
    assert chip("warn") == '<span class="chip warn">Needs a check</span>'
    assert chip("crit") == '<span class="chip crit">Blocks download</span>'
    assert "::before" not in chip("good") and "<i" not in chip("good")


class _Cell:
    def __init__(self, label, amount, sub, needs_check):
        self.label, self.amount, self.sub, self.needs_check = label, amount, sub, needs_check


def test_totals_strip_escapes_every_field():
    out = totals_strip([_Cell(HOSTILE, HOSTILE, HOSTILE, True)])
    _no_live_markup(out)
    assert out.count('class="chip warn"') == 1


def test_totals_strip_has_one_cell_per_figure_and_a_chip_only_when_flagged():
    out = totals_strip([_Cell("A", "1.00 EUR", "x", False), _Cell("B", "2.00 MAD", "", True)])
    assert out.count('class="totals-cell"') == 2
    assert out.count("chip") == 1
    assert out.startswith('<div class="totals">')


def test_wordmark_escapes_the_file_name():
    out = wordmark(HOSTILE, 8, "warn")
    _no_live_markup(out)
    assert "8 papers read" in out
    assert 'class="chip warn"' in out
    assert "📄" not in out  # a plain name in type, no emoji tile


def test_field_label_and_group_title_escape():
    _no_live_markup(field_label(HOSTILE, needs_check=True))
    _no_live_markup(group_title(HOSTILE))
    assert field_label("Issued by") == "Issued by"
    assert field_label("Total", needs_check=True) == 'Total <span class="chip warn">Needs a check</span>'


def test_the_edited_mark_is_outlined_text_not_a_chip():
    assert edited_mark() == '<span class="mark">Edited</span>'
    assert "chip" not in edited_mark()


def test_field_label_orders_the_chip_before_the_mark_and_escapes():
    assert field_label("Total", needs_check=True, edited=True) == (
        'Total <span class="chip warn">Needs a check</span> <span class="mark">Edited</span>'
    )
    assert field_label("Total", edited=True) == 'Total <span class="mark">Edited</span>'
    _no_live_markup(field_label(HOSTILE, needs_check=True, edited=True))


def test_plain_note_is_the_sans_block_for_what_the_app_says():
    assert plain("Not on the page", "note") == '<div class="pdf-note">Not on the page</div>'


def test_plain_is_an_escaped_html_block():
    out = plain(HOSTILE, "caption")
    _no_live_markup(out)
    assert out.startswith('<div class="pdf-caption">') and out.endswith("</div>")
    assert plain("Maersk A/S", "body") == '<div class="pdf-body">Maersk A/S</div>'
    assert plain("Maersk A/S", "printed") == '<div class="pdf-printed">Maersk A/S</div>'


def test_plain_starts_with_a_tag_so_markdown_does_not_parse_it():
    # A block that starts with an HTML tag is passed through as HTML, not markdown.
    assert plain("**b** [l](http://x/) ![i](http://x/p.png)").startswith("<div")


def test_plain_handles_none_and_rejects_unknown_kinds():
    assert plain(None) == '<div class="pdf-caption"></div>'
    with pytest.raises(ValueError):
        plain("x", "heading")


def test_page_label_takes_only_numbers():
    assert page_label(3, 1, 2) == '<div style="text-align:center">Page 3 · 2 of 2 for this paper</div>'
    with pytest.raises(ValueError):
        page_label("<img src=x>", 0, 1)


def test_components_do_not_import_streamlit_or_the_service():
    folder = Path(__file__).resolve().parents[2] / "app" / "ui" / "components"
    forbidden = re.compile(r"^\s*(import|from)\s+(streamlit|app\.service)\b", re.MULTILINE)
    for path in folder.glob("*.py"):
        assert not forbidden.search(path.read_text()), path.name
