"""Build design/sample.html: a static picture of the review screen.

It is drawn with the real components (app/ui/components), the real view data (app/ui/view)
and the real theme CSS (app/ui/theme), so it cannot drift from the app. The data is the
Maroc-like sample dossier from tests/ui_fixtures.py, on the customs payment tab.

    python3 design/build_sample.py

tests/unit/test_design_sample.py fails when the committed file is out of date.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.ui import lang, view  # noqa: E402
from app.ui.components import banner, esc, field_label, group_title, page_label, plain, totals_strip, wordmark  # noqa: E402
from app.ui.words import FILE_MANUAL, manual_label  # noqa: E402
from tests.ui_fixtures import maroc_dossier  # noqa: E402

THEME = ROOT / "app" / "ui" / "theme"
OUT = ROOT / "design" / "sample.html"
OPEN_TAB = 1  # the customs payment paper: two pages, its total flagged on page 3

# Layout for this static page only. Colours, radii, fonts and the component styles come from the theme.
PAGE_CSS = """
body { margin: 0; background: var(--bg); color: var(--ink); font-family: var(--font-sans); font-variant-numeric: tabular-nums; }
.page { max-width: 1280px; margin: 0 auto; padding: 24px 32px 48px; }
.row { display: flex; align-items: center; gap: 16px; }
.row.end { align-items: flex-end; }
.grow { flex: 1; }
.strip { background: var(--surface-sunken); border-top: 1px solid var(--rule); border-bottom: 1px solid var(--rule);
         margin: 16px 0; padding: 10px 16px; }
.field { width: 240px; }
.label { display: block; font-size: 14px; line-height: 20px; font-weight: 500; margin-bottom: 4px; }
.note { font-size: 13px; line-height: 18px; color: var(--ink-secondary); padding-bottom: 10px; }
.input, .select { box-sizing: border-box; width: 100%; background: var(--surface); color: var(--ink);
         border: 1px solid var(--edge); border-radius: var(--radius-sm); padding: 10px 12px;
         font: 500 15px var(--font-sans); font-variant-numeric: tabular-nums; }
.input:focus, .select:focus { outline: 2px solid var(--accent-text); outline-offset: 1px; border-color: var(--accent-text); }
.btn { font: 600 15px var(--font-sans); padding: 10px 18px; border-radius: var(--radius-md); cursor: pointer; white-space: nowrap; }
.btn.secondary { background: var(--surface); color: var(--ink); border: 1px solid var(--edge); }
.btn.primary { background: var(--accent); color: var(--on-accent); border: 1px solid var(--accent); }
.btn:hover.secondary { border-color: var(--accent-text); color: var(--accent-text); }
.btn:hover.primary { background: var(--accent-hover); border-color: var(--accent-hover); }
.btn:disabled { opacity: .5; cursor: default; }
.btn:focus-visible { outline: 2px solid var(--accent-text); outline-offset: 2px; }
.caption { font-size: 13px; line-height: 18px; color: var(--ink-secondary); }
.tabs { display: flex; border-bottom: 1px solid var(--rule); margin: 8px 0 20px; }
.tab { flex: 1 1 0; text-align: center; padding: 10px 6px 11px; font-size: 14px; line-height: 20px; font-weight: 500;
       color: var(--ink-secondary); border-bottom: 2px solid transparent; margin-bottom: -1px; white-space: nowrap; }
.tab.on { color: var(--accent-text); border-bottom-color: var(--accent); font-weight: 600; }
h2 { font-size: 20px; line-height: 28px; font-weight: 600; margin: 0; }
.cols { display: grid; grid-template-columns: 5fr 6fr; gap: 32px; align-items: start; margin-top: 12px; }
.nav { display: grid; grid-template-columns: 56px 1fr 56px; gap: 8px; align-items: center; margin-bottom: 12px; }
.nav .btn { padding: 8px 0; }
.sheet { background: #fff; border: 1px solid var(--rule); border-radius: var(--radius-lg); aspect-ratio: 3 / 4; }
.panel { background: var(--surface); border: 1px solid var(--rule); border-radius: var(--radius-lg); padding: 24px; }
.grid3 { display: grid; grid-template-columns: 1.3fr 1.6fr 1.5fr; gap: 16px; align-items: center; }
.head { padding: 10px 0 4px; }
.frow { padding: 12px 0; border-bottom: 1px solid var(--rule); }
.typed { display: grid; grid-template-columns: 1fr 1fr; gap: 14px 16px; margin: 12px 0 20px; }
.foot { display: flex; gap: 12px; align-items: center; margin-top: 20px; }
.foot .select { width: 160px; }
"""


def _css() -> str:
    parts = [(THEME / name).read_text() for name in ("fonts.css", "tokens.css", "components.css")]
    css = "\n".join(parts).replace("/app/static/fonts/", "../app/ui/static/fonts/")
    return css + PAGE_CSS


def _input(value: str, label: str) -> str:
    return f'<input class="input" value="{esc(value)}" aria-label="{esc(label)}">'


def _row(row: view.RowView) -> str:
    return (
        '<div class="frow grid3">'
        f"<div>{field_label(row.label, row.needs_check)}</div>"
        f"{_input(row.value_text, row.label)}"
        f'{plain(row.printed_text, "printed")}'
        "</div>"
    )


def render() -> str:
    lang.use("en")  # the sample is a design reference, kept in English
    dossier = maroc_dossier("sample")
    # One value shown as a person-corrected one, so the sample carries the Edited mark.
    next(doc for doc in dossier.documents if doc.id == "liquidation").fields["tax_amount"].user_value = "42266.00"
    screen = view.build(dossier)
    paper = screen.papers[OPEN_TAB]
    page = paper.default_page
    position = paper.page_numbers.index(page)

    strip_fields = "".join(
        f'<div class="field"><label class="label">{esc(label)}</label>{_input("", label)}</div>' for label in map(manual_label, FILE_MANUAL)
    )
    tabs = "".join(
        f'<div class="tab{" on" if index == OPEN_TAB else ""}">{esc(item.tab_label)}</div>'
        for index, item in enumerate(screen.papers)
    )
    typed = "".join(
        f'<div><label class="label">{esc(label)}</label>{_input("", label)}</div>' for _, label in paper.typed_fields
    )
    notes = "".join(f'<div class="caption">{esc(note)}</div>' for note in paper.typed_notes)
    can_join = paper.position > 0

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Import file: sample screen</title>
<!-- Generated by design/build_sample.py from the real components and theme. Do not edit by hand. -->
<style>
{_css()}
</style>
</head>
<body>
<!-- "stApp" is the class the component CSS keys its mono rule on; here it only switches that rule on. -->
<div class="page stApp">
  <div class="row">
    <div class="grow">{wordmark(screen.filename, screen.paper_count, screen.tier)}</div>
    <button class="btn secondary" style="width:200px">Read another file</button>
  </div>
  <div class="strip row end">{strip_fields}<div class="note">Not on any page. Saved with the open paper's Save button below.</div></div>
  <div class="row" style="margin-bottom:16px">
    <span class="caption">Export</span>
    <button class="btn secondary">Download CSV</button>
    <button class="btn primary">Download JSON</button>
  </div>
  <div class="row">
    <div class="grow">{banner(screen.tier, screen.banner_text)}</div>
    <button class="btn secondary" style="width:200px;margin-bottom:16px">Show passed checks</button>
  </div>
  {totals_strip(screen.totals)}
  <div class="tabs">{tabs}</div>
  <h2>{esc(paper.title)}</h2>
  <div style="margin-top:2px">{plain(paper.subline)}</div>
  <div class="cols">
    <div>
      <div class="nav">
        <button class="btn secondary" aria-label="Previous page">&lsaquo;</button>
        {page_label(page, position, len(paper.page_numbers))}
        <button class="btn secondary" aria-label="Next page" disabled>&rsaquo;</button>
      </div>
      <div class="sheet" role="img" aria-label="Placeholder for the scanned page"></div>
      <div class="caption" style="margin-top:8px">Placeholder for the scanned page. The app shows the real image here.</div>
    </div>
    <div class="panel">
      {group_title("Copied from the page")}
      <div class="grid3 head caption"><span>Field</span><span>Value</span><span>Printed text</span></div>
      {"".join(_row(row) for row in paper.rows)}
      <div style="margin-top:24px">{group_title("You type")}</div>
      <div class="caption" style="margin-top:8px">Not on the PDF. Leave a box empty if you do not have it yet.</div>
      {notes}
      <div class="typed">{typed}</div>
      <button class="btn primary">Save</button>
    </div>
  </div>
  <div class="foot">
    {'<button class="btn secondary">Join with the paper above</button>' if can_join else ""}
    <select class="select" aria-label="Split after"><option>Page {paper.page_numbers[0]}</option></select>
    <button class="btn secondary">Split after this page</button>
  </div>
</div>
</body>
</html>
"""


if __name__ == "__main__":
    OUT.write_text(render())
    print(f"wrote {OUT.relative_to(ROOT)}")
