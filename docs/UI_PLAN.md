# UI plan — new skin, clean structure

Draft for review. Nothing here is built yet. The look is fixed by `docs/design.md`;
this file decides **how the code is organised and in what order it is built**.

## 0. Who decided what

| Mark | Meaning |
|---|---|
| **[Decided]** | The owner chose it. Do not change without asking. |
| **[Proposed]** | Claude's suggestion. Each has an ID (P1…). Approve, change, or reject by ID. |

**[Decided]**

- Scope: the new look plus a clean, reusable structure. The three existing
  screens keep their behaviour.
- Streamlit stays. No React, no FastAPI (`AGENTS.md`).
- This document is English and lives in `docs/`.
- Claude drafts, the owner corrects.

## 1. Scope

**In**

- Apply the skin from `docs/design.md` §5 and §7.
- Split `app/ui/main.py` (685 lines, one file) into small parts.
- Make every piece of HTML that carries PDF text go through one escaping path
  (closes `design.md` D1).
- Tests for the new parts.
- Replace the stale mock `design/sample.html` and mark `docs/DESIGN_SYSTEM.md`
  as removed or archived.

**Out (deferred, listed so they are not lost)**

- `missing` and `edited` markers (`design.md` §11, decisions 3 and 4).
- Stable export area (`design.md` D6): it changes behaviour.
- French labels (`design.md` §11, decision 1).
- New screens: dossier history, settings, batch upload.
- Any change to `app/service.py` or anything below it.

## 2. Screens and states

Three screens. One URL. Which one shows depends on session state, as today.

| Screen | When | Contents | Leaves via |
|---|---|---|---|
| **Start** | no `dossier_id`, nothing pending | question, file drop zone, `Read this PDF` | Read → Reading |
| **Reading** | `pending` is set | heading, "about a minute", status block | success → Review; error → Start with message |
| **Review** | `dossier_id` is set | header, strip, export, banner, totals, tabs, paper pane | `Read another file` → Start |

States inside Review that need a defined look (all exist today):

| State | Where shown |
|---|---|
| Dossier: good / review / crit | header chip, dossier banner |
| Export blocked, override off / on | export area |
| Paper: needs a check (tab bullet, row chips, totals chip) | tab, row, totals |
| Paper: one page / several pages | page nav shown only when several |
| Paper: broker invoice (per-line tax and reason code) | form panel |
| Paper: customs (extra `SAP reference`) | form panel |
| Paper: no fields read (fake provider, empty reading) | form panel shows blank rows |
| Dossier could not be opened / has no papers | single message |
| PDF rejected / runtime error while reading | message + `Back` |

## 3. Layers

One direction only. A layer may use the ones below it, never above.

```
screens/      one function per screen; the only place that calls app/service.py
widgets/      pieces that call Streamlit (st.*) and return what the person did
view.py       pure: turns a Dossier into plain view data (tiers, labels, rows)
components/   pure: view data -> HTML string; escapes everything; no st, no service
theme/        CSS files + loader; the only place with colours and sizes
words.py      existing: the paper's terms and sentences
```

Rules:

- `components/` and `view.py` import neither `streamlit` nor `app.service`.
  That is what makes them testable and keeps business rules out of the UI
  (`AGENTS.md`).
- Severity → tier (`error`→crit, `warning`→review, none→good) lives in
  `view.py`, once.
- **Every string that came from a PDF is escaped inside `components/`, never by
  the caller.** A component takes plain text and returns safe HTML. PDF text is
  never passed to a markdown-rendering call (`st.write`, `st.caption`): Streamlit's
  markdown makes links and externally loaded images, even from a bare URL.
  A line of PDF text on its own goes through `plain()`.
- Only `theme/` contains hex values or pixel sizes.

## 4. Folder layout **[Proposed P1]**

```
app/ui/
  main.py               thin: page config, theme, route to a screen
  state.py              session_state keys + typed get/set (one place)
  view.py               Dossier -> DossierView / PaperView (pure)
  words.py              (exists, unchanged)
  static/fonts/         IBM Plex woff2 + OFL license (served at /app/static/fonts/)
  theme/
    __init__.py         inject(): reads the css files, one st.markdown call
    tokens.css          :root + dark values from design.md §5.2 only
    components.css      banner, chip, totals, panel, field rows
    streamlit.css       overrides of Streamlit widgets (data-testid selectors)
  components/           pure HTML builders
    text.py   banner.py   chip.py   totals.py   field_label.py   wordmark.py
    page_label.py   icons.py   (badge.py arrives with the new skin, step 5)
  widgets/              st.* pieces
    header.py   strip.py   export_area.py   page_viewer.py
    paper_form.py   check_list.py   join_split.py
  screens/
    start.py   reading.py   review.py
```

Naming constraint: do **not** create a folder called `pages/` — Streamlit would
turn it into automatic routes. Do not name any file `app.py` (it broke imports
before, commit `c6329ac`).

`.streamlit/` is in `.gitignore`, so a Streamlit theme file cannot ship with the
repo. All theming is injected CSS, as today.

## 5. Reusable parts

Pure builders in `components/` (each returns a string):

| Component | Input | Used on |
|---|---|---|
| `banner(tier, text)` | tier, plain text | dossier banner, paper checks |
| `chip(tier)` | tier → fixed word | header, rows, totals |
| `badge(tier)` | tier → square glyph | inside banner |
| `totals_strip(cells)` | list of label, figure, sub-line, tier | review top |
| `field_label(text, tier)` | label + optional chip | form rows |
| `wordmark(name, file, count, tier)` | text | header |

Widgets in `widgets/` (call Streamlit):

| Widget | Returns |
|---|---|
| `header(view)` | whether `Read another file` was pressed |
| `strip(manual)` | typed order number and exchange rate |
| `export_area(dossier)` | nothing (renders buttons or override box) |
| `page_viewer(paper)` | nothing (renders nav + image, keeps page in state) |
| `paper_form(paper)` | typed values and corrections on Save |
| `check_list(items)` | nothing |
| `join_split(paper)` | which action was pressed |

The same `chip`, `banner`, and `field_label` are used on every paper type, so a
new document type adds a name in `words.py` and a field list, not new UI.

## 6. View data **[Proposed P2]**

`view.py` converts once, so screens do not poke at `FieldValue` internals.

```
DossierView   filename, paper_count, tier, banner_text, totals[], papers[]
PaperView     id, tab_label, title, subline, pages, default_page, rows[], lines[],
              typed_fields[], checks[]
RowView       key, label, value_text, printed_text, tier|None
```

It holds the logic that is in `main.py` today: `_display`, `_currency`,
`_headline_amount`, `_default_page`, `_tab_label`, `_paper_manual_fields`,
`_check_sentence`. Moved, not rewritten.

## 7. Streamlit specifics

- CSS is loaded from files with `Path.read_text()` and injected once per run.
- Widget overrides use `data-testid` selectors and are pinned to
  `streamlit==1.49.1`. A version bump means a full visual pass.
- Widget keys keep today's names (`value-{doc}-{key}`, `paper-{doc}:{key}`,
  `page-{doc}`) so session state keeps working during the move.
- Tabs, forms, columns, `download_button`, `status` stay native widgets.
- Streamlit is **not installed in this working environment**. Step 0 installs it.
- Fonts are served by Streamlit's static folder, which needs
  `--server.enableStaticServing true` (now in the README run command). Without it
  the screen falls back to system fonts.

## 8. Tests **[Proposed P3]**

| Test | Proves |
|---|---|
| `components/*` unit tests | each builder escapes `<`, `&`, quotes; a hostile issuer name stays text |
| `test_ui_html_safety.py` | every `unsafe_allow_html=True` call gets a constant or a component builder, never an f-string |
| `view.py` unit tests | severity→tier; headline amount; default page opens on the flagged field's page; broker/customs field lists |
| `test_design_rules.py` | the CSS has no side-bar borders, no `box-shadow`, no pill radii, no Inter, no indigo; only `theme/` has hex colours |
| Streamlit `AppTest` smoke | each screen renders with the fake provider and a seeded dossier; no exceptions |
| Existing suite | stays green; nothing below `app/ui/` changes |

A seeded dossier is needed for the smoke tests and for screenshots: the fake
provider reads nothing, so most rows would be blank. Build it from the Maroc
values already used in `tests/validation/test_maroc_answer_key.py`.

Visual check: headless Chromium screenshots of each screen in light and dark,
before and after. Kept out of the repo (no new dependency).

## 9. Order of work **[Proposed P4]**

Each step ends with tests green and the app still running. Steps 1–3 change
nothing the user can see.

| # | Step | Visible change |
|---|---|---|
| 0 | Install requirements, run tests, run the app, take "before" screenshots | none |
| 1 | `components/` + escaping tests; use them in `main.py` for card text only (fixes D1) | none |
| 2 | Move CSS verbatim into `theme/*.css`; load from files | none |
| 3 | `view.py` + `state.py`; move helpers out of `main.py` | none |
| 4 | Split into `screens/` and `widgets/`; `main.py` becomes the router; `AppTest` smoke | none |
| 5 | **Skin switch:** new tokens, fonts, banner, chips, totals strip, flat panel, wordmark, radii | **yes** |
| 6 | Visual pass in both themes with the seeded dossier; fix leaks of Streamlit's own styling | yes |
| 7 | Replace `design/sample.html`; retire `docs/DESIGN_SYSTEM.md`; update `docs/design.md` status | none |

Why the skin comes late: after steps 1–4 the whole look lives in `theme/` and
`components/`, so step 5 is a contained change that can be reviewed and reverted
alone.

## 10. Risks

| Risk | Handling |
|---|---|
| Streamlit's default styles leak through (inputs, tabs, uploader) | step 6 checks every widget in both themes |
| Moving widget keys loses typed values on a tab switch (`design.md` D7) | keep key names; add an `AppTest` for it |
| `st.form` + tabs rerun behaviour differs from what the code assumes | covered by the same test |
| Fonts load from Google | open decision below |
| Seeded dossier drifts from real extraction output | build it from the existing Maroc answer-key values |

## 11. Still open — your call

1. **Fonts: self-host or Google Fonts?** Today's code uses Google Fonts.
2. **Preview/form width.** The mock uses 5:6; the app has 2:1, which squeezes the
   form. This is a layout change. Keep 2:1 or move to 5:6?
3. **Approve P1–P4**, or say which to change.

## 12. Definition of done

- Existing tests and the new ones pass.
- The three screens look like the mock in both themes.
- No PDF-derived string reaches HTML unescaped.
- `main.py` is a router of under ~60 lines; no file in `app/ui/` over ~200 lines.
- Only `theme/` has colours and sizes.
- `docs/design.md` and this file match the code.

## 13. Step 0 results

Run on Python 3.13 with the pinned requirements (`streamlit==1.49.1`).

- **Tests:** 24 passed, before any change.
- **App:** starts on port 8765 with the fake provider.
- **Seeded dossier:** the fake provider reads nothing, so the Review screen was
  seeded with a Maroc-like dossier (8 papers, one failing line-sum check on the
  Maersk invoice) through a throwaway launcher outside the repo. This becomes a
  real test fixture in step 4.
- **"Before" screenshots:** Start and Review, light and dark, kept outside the
  repo.

Seen on the live screen, beyond what `design.md` already lists:

| # | Finding | Fixed by |
|---|---|---|
| F1 | The crescent on the banner is real (`design.md` D2). | step 5 |
| F2 | The *Field / Value / Printed text* header sits **outside** the form panel and does not line up with its columns. | step 5 (header moves inside the panel) |
| F3 | In the 1/3-width form column, labels wrap ("Invoice number") and the `Needs a check` tag breaks onto two lines. | step 5, and open decision 2 (width ratio) |
| F4 | A broker invoice shows seven line rows, each with two boxes, which makes the panel about 1,300px tall. | not in scope; noted for later |
| F5 | The drop zone says **"Limit 200MB per file"**, but the app limit is 30 MB. It is Streamlit's default text. | step 6; needs CSS or a replacement, since `.streamlit/` is not in the repo |
| F6 | When a check blocks the download, the export area shows only a checkbox, no buttons (`design.md` D6, deferred). | later |
| F7 | In this sandbox Google Fonts did not load, so a fallback font rendered. Open decision 1 (self-host) matters. | decision |

## 14. Step 1 results (done)

**Fonts (decided: in the repo).** IBM Plex Sans 400/500/600 and Mono 400/500, Latin
and Latin Extended (for ı, ş, Ş), 188 KB, in `app/ui/static/fonts/` with the SIL OFL
license. Source: the `@fontsource` packages, version 5.1.0. Not wired into the CSS yet;
that happens with the new skin in step 5. Checked that Streamlit serves them (HTTP 200,
`font/woff2`) when started with `--server.enableStaticServing true`.

**D1 reproduced, then closed.** A dossier whose issuer name was
`<img src=x id=pwn-html> **b** [l](http://evil.example/) ![i](http://evil.example/p.png)`
was loaded on the live screen.

| Probe | Before | After |
|---|---|---|
| raw `<img>` element in the page | 1 | 0 |
| images loading from the outside host | 4 | 0 |
| links to the outside host | 5 | 0 |
| bold text from the document | 5 | 0 |

The text still shows, as plain text. The first fix (escaping markdown characters) left
bare URLs clickable, because Streamlit auto-links them; the final fix renders PDF text
only as escaped HTML blocks.

**What changed in the code.** New `app/ui/components/` (pure builders: `banner`,
`tag`, `status_pill`, `summary_card`, `wordmark`, `field_label`, `group_title`,
`page_label`, `plain`, `esc`) and `main.py` now calls them. Tests went from 24 to 44.

**Visual check.** Same seeded dossier, before and after, light and dark: the header,
export area, banner and summary cards are pixel-identical. About 0.4% of pixels differ,
all in the paper pane: printed text sits 1-3 px differently, and the line numbers on
broker invoices ("1.") no longer hang as a list marker. Layout is unchanged.

**New findings**

| # | Finding | Fixed by |
|---|---|---|
| F8 | Streamlit forces its own font (Source Sans) on its text, so the CSS `font-family` set on `.stApp` never reached it; the app has not been rendering Inter anywhere. | step 5: apply the family to Streamlit's text elements |
| F9 | Streamlit gives every markdown block a -16px bottom margin that a `<p>` cancels; any raw `<div>` block needs the margin written out. | already handled for `.pdf-caption` and `.pdf-body`; remember for new blocks |

## 15. Step 2 results (done)

The 259 lines of CSS that sat inside `main.py` are now three files in `app/ui/theme/`,
moved without changing a rule:

| File | Lines | Holds |
|---|---|---|
| `tokens.css` | 68 | colours, radii, shadows; light, dark by OS setting, dark by `[data-theme]` |
| `streamlit.css` | 147 | overrides of Streamlit widgets (buttons, inputs, tabs, drop zone, form panel, header strip) |
| `components.css` | 49 | banner, tag, status pill, brand mark, info glyph, group title, PDF text blocks, summary card |

`theme.inject()` reads the files on every run (so a CSS edit shows after a page refresh)
and writes one `<style>` element. `main.py` went from about 690 lines to 399.

**How it was checked**

- A script compared every non-blank CSS line before and after. It caught one line left
  behind in the first split; fixed, and then nothing was lost and nothing was added.
- Same seeded dossier and the Start screen, light and dark: **all four screenshots are
  pixel-identical** to the step 1 / original ones.
- Tests: 44 to 48. They check that the three files load in order, that both themes are
  defined, that every `var(--x)` used is defined, and that no CSS or hex colour is left
  in `app/ui/*.py` outside `theme/`.

The old Google Fonts `@import` and the Inter family are still in `tokens.css` on purpose;
they change with the skin in step 5.
