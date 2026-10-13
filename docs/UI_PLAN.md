# UI plan — new skin, clean structure

> **Status: done (steps 0 to 7, plus D6, the missing / edited markers and the French / English switch).** Sections 0 to 12 are the
> plan as agreed; sections 13 to 23 record what each step did and how it was checked.

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
    header.py   strip.py   export.py   page_viewer.py
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
| `header(screen)` | whether `Read another file` was pressed |
| `strip(manual)` | typed order number and exchange rate |
| `export_override()` / `export_buttons(csv, json)` | whether "download anyway" is ticked / nothing |
| `page_viewer(paper, image_for)` | nothing (renders nav + image, keeps the page in state; the screen supplies the image) |
| `paper_form(paper, manual)` | a `FormResult` on Save, else None |
| `check_list(paper)` | nothing |
| `join_split(paper)` | a `JoinSplitAction`, or None |

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

## 16. Step 3 results (done)

**What moved.** Everything in `main.py` that decides *what to show* now lives in two
modules; `main.py` only draws it (about 690 lines at the start of the plan, 399 after
step 2, **250 now**).

| Module | Lines | Holds |
|---|---|---|
| `app/ui/view.py` | 309 | pure: `build(dossier)` returns frozen `DossierView`, `PaperView`, `RowView`, `LineView`, `CheckView`, `TotalsCell`. The helpers that were in `main.py` (`display`, `headline_amount`, `check_sentence`, `tab_label`, `default_page`, `paper_manual_fields`) moved here unchanged, plus severity to tier (`check_tier`, `dossier_tier`), the banner sentence, and the totals cells. |
| `app/ui/state.py` | 110 | every `st.session_state` entry and every widget key, spelled once |

`view.py` imports neither Streamlit nor the service (a test checks it).

**Test data.** `tests/ui_fixtures.py` builds the Maroc-like dossier (8 papers, optional
blocking error) so tests and the browser checks use the same data. It will also feed the
`AppTest` smoke tests in step 4.

**Checks.** Tests went from 48 to 82. Behaviour was checked in a real browser before and
after the move, with the same script: it opens all 8 tabs, steps a two-page paper back
one page, switches tabs and returns, types a value without saving and switches tabs,
toggles *Show passed checks*, corrects a total and presses Save.

- The recorded results are **identical** (page labels, the remembered page, the typed
  value surviving a tab switch, the toggle, the corrected total `44,004.00 MAD` to
  `50,000.00 MAD`, the open tab after Save).
- 8 of 9 screenshots are pixel-identical. The ninth (after Save) differs in 91 pixels
  along input borders; the content is the same, so this looks like anti-aliasing.
- The hostile-dossier probe from step 1 is still clean.

**Settled.** `design.md` D7 (does a typed but unsaved value survive switching papers?)
**does hold today**, and the widget keys that make it hold are now fixed in `state.py` and
covered by a test that pins their spelling.

## 17. Step 4 results (done)

`main.py` is now a router of 18 lines. The screens and the pieces they use are split out:

| Folder | Files | Notes |
|---|---|---|
| `app/ui/screens/` | `start.py` (16), `reading.py` (32), `review.py` (98) | the only code in `app/ui` that calls `app.service` |
| `app/ui/widgets/` | `header`, `strip`, `export`, `page_viewer`, `paper_form`, `check_list`, `join_split` (13 to 75 lines each) | draw something, return what the person did; never save |

Two small design decisions made while building, both inside the plan's rules:

- `page_viewer` takes an `image_for(page)` function from the screen instead of calling the
  service itself, so widgets stay free of service calls.
- `export_area` became two widgets (`export_override`, `export_buttons`); the screen decides
  which to show and does the saving.

**Checks**

- Tests: 82 to 105. New: `test_ui_layers.py` enforces the layer rules on import lines (only
  screens call the service; `view`, `words`, `components` never import Streamlit; lower layers
  never import higher ones; `main.py` stays a router; no file becomes a monolith again) and
  `test_ui_screens.py` runs the real screens with Streamlit's `AppTest`: start and reading
  (good file, bad file, back), the review screen with 8 tabs, the blocked-export override, show
  passed checks, page stepping, saving a correction (the original value is kept), join, split,
  a missing dossier, read another file, and a hostile issuer name.
- Browser, same scripted tour as step 3: the behaviour log is **identical**, and all 10 tour
  screenshots plus the review and start screens in light and dark are **pixel-identical**
  (this time even the Save screenshot). The hostile-dossier probe is still clean.
- Real uploads through the start screen: a valid PDF opens a review screen; a non-PDF shows
  "File was not accepted. Upload one PDF." with a Back button.

The code is now laid out as planned; what remains in `docs/UI_PLAN.md` section 9 is the
skin (step 5), the visual pass (step 6), and the clean-up of the old mock and doc (step 7).

## 18. Step 5 results (done): the new skin

The look in `docs/design.md` sections 5 and 7 is now the look of the app.

**What changed on screen**

| Area | Before | Now |
|---|---|---|
| Colours | indigo, zinc greys, pastel status tints | paper and desk neutrals, ballpoint blue for actions, three status colours as fills (`tokens.css`) |
| Type | Inter, never actually applied (F8) | IBM Plex Sans forced onto Streamlit's own text; Plex Mono for the *Printed text* column only; served from `app/ui/static/fonts` |
| Banner | tinted box with a coloured bar on its edge (the crescent) | paper, hairline, square badge with a glyph, sentence in ink |
| Status labels | pale pill with a dot | filled chip, no dot; same chip in the header |
| Headline figures | four boxed cards with shadows | one ruled strip |
| Form panel | lifted card with a shadow | flat paper with a hairline; column headings moved inside it (F2); rows divided by rules and centred on the input |
| Header | emoji tile + title | plain wordmark |
| Radii, depth | 10 / 14 / 20 px, shadows | 3 / 4 / 6 px, no shadows anywhere |
| Page and form widths | 2 : 1 (form squeezed, F3) | 5 : 6 |
| Header strip | a small (i) glyph with a tooltip | the note written out |
| Messages | Streamlit's tinted alert boxes | our banner |
| Upload box | "Limit 200MB" (F5) | "Limit 30MB", from `--server.maxUploadSize 30` in the README run command |

**Guards added** (`tests/unit/test_design_rules.py`, 14 tests): no side-bar borders, no
shadows, no radius above 6 px or circle or pill, no gradients, no Inter and no outside font
host, none of the old indigo, zinc or pastel hex values, hex colours only in `tokens.css`,
no emoji in screen code, every font file the CSS names exists, the README run command keeps
the upload limit equal to `max_upload_bytes`, and **contrast floors computed from the tokens
for both themes** (text 4.5:1, control borders and focus rings 3:1).

**Checks.** Tests: 105 to 119, all green. The same scripted browser tour as steps 3 and 4
gives an identical behaviour log. The injection probe is clean. Real uploads still work (a
valid PDF opens a review screen; a non-PDF shows the banner and a Back button).

**Left for step 6** (the visual pass): the reading screen's status block still has a
slightly tinted header from Streamlit; the drop zone, checkbox when ticked, and select menu
popup need a look in both themes; the export area still swaps its buttons for the override
box (D6, deferred); Streamlit's own element spacing around the banner row.

## 19. Step 6 results (done): the visual pass

A gallery of 12 states was captured in light and dark with the seeded dossiers (empty start,
file chosen, "choose a PDF first" warning, reading error, blocked dossier, focused input,
hovered button, shipping tab with checks shown, open select menu, customs tab, clean dossier,
override ticked) and read side by side.

**Fixed**

- The reading screen's status block kept a pale blue header from Streamlit; it now follows
  the paper surface in both themes.
- After "download anyway", the two download buttons sat far apart (each in a wide, mostly
  empty column); they now fill their columns and sit side by side.

**Checked and already right in both themes**: the drop zone and the chosen-file row, the
"Limit 30MB" text, the unticked override box, the banner and its badge, chips, the totals
strip, tabs (selected underline, hover), page buttons (enabled and disabled), inputs, the
select and its menu (the menu follows the operating system theme), error and warning banners.

**Keyboard.** Tabbing through the clean-dossier screen gives 23 interactive stops in each
theme; every one shows a solid 2 px ring in `accent-text`. The only stop without a ring is
Streamlit's scrollable page container, which is not a control. `test_design_rules.py` now
fails if a focus ring is removed (`outline: none` or `0`).

Tests: 119 to 120.

**New finding D9** (in `docs/design.md` section 10): the header chip is decided by validation
results only, so a dossier with flagged fields but passing checks says "Ready to download"
while rows and totals say "Needs a check". `design.md` section 4 says a flagged field makes
the dossier `warn`. This is a behaviour change, so it is left for a decision.

**Not touched, by plan**: D6, the export area still swaps its buttons for the override box.

## 20. Step 7 results (done): D9 and the clean-up

**D9 fixed.** The dossier state in the header (and the banner under it) now counts values in
`review`. `view.dossier_tier` is `crit` for a failed check with severity `error`, `warn` for any
other failed check *or any value in `review`*, and `good` only when neither exists. With no
failed check the banner counts values: `3 value(s) might need a second look before you
download.` With failed checks it keeps counting checks. In the browser, the sample dossier
(three flagged totals, all checks passing) used to say `Ready to download` and now says
`Needs a check`. Tests: 120 to 125 (the new ones cover one flagged value, flagged values with
a failed check, and a blocking error winning).

**Clean-up**

- `docs/DESIGN_SYSTEM.md` is deleted (replaced by `docs/design.md`).
- `design/sample.html` is replaced by a page **generated** by `design/build_sample.py` from the
  real components, view data and theme CSS, so it cannot drift. Two tests: the committed file
  must equal a fresh build, and it must contain the new components and none of the old look.
  (Tests 125 to 127.)
- `docs/design.md`: the document table, the fonts note (now in the repo), the status of every
  finding D1 to D9, the open-decision list and the order of work are brought up to date.
- `docs/UI_REVIEW.md` gets a short history note at the top; its text is kept as written.
- Not touched, by decision: D6 (the export area swaps its buttons for the override box), the
  `missing` and `edited` markers, French labels, and the check against a real dossier.

**Whole-plan check.** 127 tests pass. The scripted browser tour (8 tabs, page stepping, an
unsaved value surviving a tab switch, show passed checks, correcting a total and saving) gives
the same behaviour log as at step 3.

## 21. After the plan: D6, a stable export area (done)

The export row used to change shape: while errors blocked the download it showed only a
"download anyway" box; ticking it made the box vanish and two buttons appear. Measured in the
browser before the change, ticking moved the banner, the totals strip and the tabs **down 20 px**
and made two buttons appear from nowhere.

**Now** the row is `[Download CSV] [Download JSON] ☐ Download anyway` in every state. While errors
block, the buttons are disabled and the box is unticked; ticking it saves the choice and enables
the buttons; unticking disables them again. With no blocking error there is no box and the buttons
are enabled. `widgets.export_row` draws it and `review._export_area` decides what is allowed.

**Measured after:** banner, totals, tabs, both buttons and the box sit at identical coordinates
before and after a tick; only `disabled` and `checked` change.

**Found and fixed on the way**

- A first version passed the saved flag as the box's `value`. A changing value gives the box a new
  identity, so the page redrew it and **keyboard focus was lost after every press of Space**. The
  box now starts from the saved flag once per dossier (`state.init_override`) and keeps one
  identity; three presses of Space in a row toggle it three times with focus staying on the box.
- The ticked box looked empty: the CSS set the `background` shorthand, which erased the tick image
  Streamlit draws on the box. It now sets only the colour; ticked is an accent fill, and the box
  has the same 2 px focus ring as the other controls.
- The box key now includes the dossier id, so a tick cannot carry over to the next file.

Tests: 127 to 135 (disabled and enabled buttons in each state, tick, untick, a saved override
reopened ticked, one dossier's tick not affecting another, the key pinned, the checkbox CSS).
The scripted tour, the injection probe and real uploads give the same results as before.

## 22. After the plan: "Not on the page" and "Edited" (done)

Two small additions from `docs/design.md` section 11, decisions 3 and 4, both UI only.

- **Not on the page.** A field the reader found nothing for (status `missing`, no value, nothing
  typed) used to be a blank box beside a blank printed-text cell, which looks the same as "nobody
  looked". The printed-text cell now says `Not on the page` in a quiet sans caption, clearly not
  the mono face used for paper text. The value box stays blank; nothing is invented. Once a person
  types a value the row is no longer called missing.
- **Edited.** A value whose `user_value` is set shows a small **outlined** `Edited` label after the
  row label (after the `Needs a check` chip if there is one). It is outlined, not filled, because
  it is information and not a status tier. It appears after Save: a Streamlit form keeps unsaved
  typing in the browser, so the server cannot know about it before then. Clearing a value counts
  as an edit and is not called missing.

Where: `RowView.missing` and `RowView.edited` in `view.py`; `edited_mark` and the `note` kind of
`plain` in `components/`; `NOT_ON_THE_PAGE` in `words.py`; `.mark` and `.pdf-note` in
`components.css`; the row in `widgets/paper_form.py`. The exports are untouched.

Checks: tests 135 to 147 (the flags in each case, a test that the new words never appear in the
JSON or the CSV, the markup, the AppTest screens), `design/sample.html` regenerated (it now carries
one Edited row). In the browser the licence tab shows two `Not on the page` rows in both themes,
and a saved correction shows `Edited` after the label. The scripted tour and the injection probe
give the same results as before.

## 23. French and English (design.md §11, decision 1)

**Decided by the owner:** a FR / EN switch, not French only. French on first load. Terms: Claude
drafts, the accountants correct.

**Built**

- `app/ui/lang/`: `__init__.py` (`t`, `tn`, `use`, `has`), `en.py`, `fr.py`. One flat dictionary per
  language, the same keys. The language is a context variable set at the top of every run
  (`main.py`), so two sessions never share it, and pure code reads it without importing Streamlit.
- Every sentence that was a literal in `words.py`, `view.py`, `components/`, `widgets/` and
  `screens/` is now a key. `TIER_WORDS` and `NOT_ON_THE_PAGE` became functions (`tier_word`,
  `not_on_the_page`). `file_status` (unused) was removed.
- Checks are matched by rule id, passed ones too (they used to show validation's English message).
  Refusals from `render_pdf` are mapped in `words.rejection_text`; an unknown one shows as it came.
  Nothing below the UI changed.
- `widgets/language.py`: the switch. Its label is fixed ("Langue / Language"): a label that follows
  the language changes the widget's identity and Streamlit resets it (found in the browser, pinned by
  a test).
- "1 papers read" now reads "1 paper read" / "1 pièce lue".

**Checked**

- Tests: both catalogs have the same keys and slots; every key in code exists and none is dead; a
  French view holds no English sentence; every refusal `render_pdf` can give has a French sentence;
  the switch survives a rerun; one thread cannot change another's language.
- Browser, 1440 px, both languages and both themes: no clipped text, no horizontal scroll, the
  longest French strings (export row, banners, totals) fit.

**Left alone, on purpose**: JSON / CSV, money formatting, Streamlit's own uploader text, and the
page `lang` attribute (Streamlit sets it).
