# Design language

How the Import dossier reader looks, sounds, and behaves — and why. This is the
rulebook to check a change against before it ships.

It sits on top of two documents that already exist and does not repeat them:

| Document | Answers | Status |
|---|---|---|
| `docs/UI_REVIEW.md` | What is on the screen and where | Layout decisions; partly superseded (see §10) |
| `docs/DESIGN_SYSTEM.md` | Which hex, size, and radius | Implemented in `app/ui/main.py` |
| **this file** | Why, what each thing means, and the rules for new work | Source of intent |

If this file and the CSS disagree about a *value*, the CSS in `app/ui/main.py`
wins and this file is stale. If they disagree about a *rule*, this file wins and
the code is a bug. §10 lists every disagreement found today.

---

## 1. The product, as a design problem

Two accountants take a ~10-page scanned customs pack, six to eight papers in one
PDF, and key it into SAP by hand. 50–80 packs a month, 20–35 minutes each. The
screen does one narrow part of that job: show what was read off each paper, let
the person fix a misread value, let them type the few SAP fields no paper
prints, and hand them JSON and CSV.

What this means for the design:

- **The work is comparison, not browsing.** The most repeated action is: look at
  the page, look at the value, decide if they match. Every layout choice serves
  that glance.
- **The users are experts at the papers and strangers to the model.** They know
  what a customs liquidation looks like. They do not know why the system is
  unsure, and should never have to.
- **A wrong number that looks right costs more than a slow screen.** The design
  prefers a visible doubt over a smooth finish.
- **Long sessions, daily.** Comfortable density, no novelty, nothing that
  demands attention without a reason.

**Personality: a careful second pair of eyes.** Calm, exact, plain-spoken. It
points at the thing worth a look and otherwise stays out of the way.

**It is not:** an AI product. No sparkle, no "magic", no assistant voice, no
confidence meter, no progress theatre. The model is plumbing. The screen talks
about *papers and values*, never about *the AI*.

---

## 2. Principles

Each principle has a test. A change that fails a test needs a reason written in
the PR.

1. **The paper is the truth; the screen is the comparison.**
   Value, printed text, and page image are always reachable together. The page
   shown is a page the paper actually spans, and a field flagged `review` opens
   on the page it was read from.
   *Test: can the clerk verify one flagged value without leaving the pane?*

2. **Never fake certainty.**
   A missing field stays empty — not `0`, not `—` pretending to be a value, not a
   placeholder that could be exported. No percentages, no scores, no "likely".
   Status is exactly `high`, `review`, or `missing` (`docs/ARCHITECTURE.md`).
   *Test: could any pixel on screen be read as a confidence the system doesn't have?*

3. **Quiet by default; color means "look here".**
   `high` has no decoration at all. Only `review`, blocking errors, and the
   dossier state earn color. If most rows are colored, nothing is.
   *Test: squint at a healthy dossier — is the screen almost entirely neutral?*

4. **One thing at a time.**
   One paper open, two groups (copied, typed), one Save per paper, one export
   area. No second place to do the same job.
   *Test: for any action, is there exactly one button for it on screen?*

5. **State is never color alone.**
   Every status ships a word, and tier status also ships an icon or dot shape.
   *Test: view it in greyscale — can you still tell good, check, and blocked apart?*

6. **Stable places.**
   Controls don't move, appear, or swap when data changes. Disabled beats hidden.
   *Test: after any state change, is every button where it was?*

7. **Say it the way the paper says it.**
   Labels are the paper's terms in plain words ("Issued by", "Bill of lading",
   "Customs payment"). No rule ids, no field keys, no model vocabulary on screen.

8. **Document text is data, never markup.**
   Anything read from a PDF — names, numbers, line descriptions, raw text — is
   escaped before it touches HTML. It is the same rule as `AGENTS.md`'s
   "untrusted documents", applied to pixels.
   *Test: does any `unsafe_allow_html=True` string contain text that came from a PDF?*

---

## 3. Voice and content

Plain, short, specific. Sentence case everywhere. No exclamation marks, no
emoji, no "Oops", no "Please note".

**Formulas**

| Kind | Formula | Example |
|---|---|---|
| Check result | `Paper: what is wrong.` | `Shipping invoice: the lines on the page do not add up to the amount before tax.` |
| Dossier-level check | what is wrong, no prefix | `The bill of lading is not the same on every paper.` |
| Banner | count + consequence | `2 item(s) block the download until you check them.` |
| Button | verb (+ object when ambiguous) | `Save`, `Read this PDF`, `Download JSON`, `Join with the paper above` |
| Hint under a field | why it's empty / what to do | `Not on the PDF. Leave a box empty if you do not have it yet.` |
| Error | what happened, then the way out, one sentence each | `This file could not be opened.` + **Back** |

**Terms** live in `app/ui/words.py` and nowhere else. A new document type or
field adds its name there. Do not put a user-facing string in `main.py` that
`words.py` could own.

**Numbers**

- Money: thousands separator, two decimals, currency code after, tabular
  figures: `18,921.09 EUR`. Currency is shown when known, omitted when not —
  never guessed.
- Pages: `Page 3`, `Pages 2–3`, `Pages 2, 4`.
- Dates: shown as the paper prints them in *Printed text*; the *Value* column
  carries the normalized form. Never reformat the printed text.
- Empty is empty. The card summary says `Not read` only where a whole figure is
  absent from a card; a field row stays blank.

**Language.** The screen is English today. `UI_REVIEW.md` §7 recommends French
(the papers are French, SAP may be French). That decision is still open — see
§11. Until it is made, write new strings in English and keep them in
`words.py` so the switch is one file.

---

## 4. Status language

The single most important table in this document. Every status in the data maps
to one visual tier, one word, one shape.

| Tier | Meaning | Word | Shape | Data source |
|---|---|---|---|---|
| **good** | Ready, check passed | `Ready to download` | circle-check icon / dot | no failed validation |
| **warn** | Worth a second look, does not block | `Needs a check` | triangle icon / dot | field `review`; validation `severity: warning`; boundary `review` |
| **crit** | Blocks the download | `Blocks download` | circle-x icon / dot | validation `severity: error`, `status: failed` |
| *(none)* | Read and consistent | — | no decoration | field `high` |
| *(none, see §11)* | Not on the page | — | blank value | field `missing` |

Rules:

- **`high` is silent.** It is the normal state; marking it dilutes everything else.
- **Tier follows severity, not volume.** One blocking error makes the dossier
  `crit` regardless of how many warnings exist.
- **Dossier state is a pill in the header; item state is a tag on the row.**
  Never put a banner where a tag will do.
- **A blocked export is overridable by a person, not by the app.** The override
  is an explicit, stored choice (`export_with_errors`).
- **Two word forms per tier, used consistently:** header pill (`Needs a check`),
  row tag (`Needs a check`), banner sentence (count + consequence).

---

## 5. Visual foundations

Values are in `docs/DESIGN_SYSTEM.md` and `app/ui/main.py`. This section is
*which token for which job*.

### Color roles

| Job | Token | Never use for |
|---|---|---|
| Page ground | `--bg` | cards |
| Raised content (cards, form panel, inputs) | `--surface` | page ground |
| Footer-ish strips, header strip | `--surface-sunken` | text backgrounds in dark mode (it equals `--bg` there) |
| Primary text, values | `--ink` | captions |
| Labels, captions, printed text | `--ink-secondary` | — |
| Hints that repeat something visible | `--ink-muted` | any value the clerk must read (2.6:1 in light) |
| The one action on a screen, selected state, focus | `--accent` | status |
| Links / text on bare ground | `--accent-text` | fills |
| Status | `--{good,warn,crit}-{text,bg,strong}` | decoration, emphasis |
| Hairlines | `--border` | the only cue that something is an input (see §8) |

There is one accent. Indigo means "you can act here" and "this is selected". It
never means a status. Status never uses indigo.

### Type

One family: **Inter**, fallback system sans. Weight does the work; no serif, no
italics. Tabular figures on, globally, so every amount column aligns.

| Role | Size / line · weight | Used for |
|---|---|---|
| Page title | 26 / 32 · 700 | `st.header` |
| Paper title | 20 / 28 · 600 | `st.subheader` per paper |
| Card amount | 22 · 700 | summary tile figure |
| Value / body | 15 / 22 · 500 | inputs, button labels, row values |
| Field label | 14 / 20 · 500 | row labels |
| Caption | 13 / 18 · 400 | page counts, printed text, hints |
| Group label | 12 / 16 · 600 · caps · +0.06em | `COPIED FROM THE PAGE`, `YOU TYPE` |
| Tag | 12 · 600 | status tags |

Nothing below 12px. (The header status pill is 11.5px today — see §10.)

### Space, shape, depth

- 4px base; the working range is 16–24 for card padding and between field rows,
  4–8 for icon-to-label gaps.
- Radius scales with size: 10 (tags, inputs) · 14 (buttons) · 20 (cards, panels,
  banners) · pill (header status, dots).
- Light mode lifts with soft shadow; dark mode lifts with a lighter surface and a
  hairline. The form panel is the one `--shadow-md` element — it is the thing
  being worked on.
- No gradients. No decorative imagery. No illustration. No emoji.

### Icons

Inline SVG, 16×16, 1.75 stroke, round caps, `currentColor`. Four meanings only:
good (circle-check), warn (triangle), crit (circle-x), page navigation
(chevrons — Streamlit's Material chevrons). No icon font, no new dependency. An
icon is never the only carrier of a meaning (principle 5).

### Motion

None designed. Streamlit reruns repaint the page; do not add transitions to hide
that. The only waiting state is the reading screen, which says how long it takes
("about a minute") instead of animating.

---

## 6. Screens and anatomy

Streamlit, wide layout, sidebar collapsed, Streamlit chrome hidden. One page,
three states.

### 6.1 Start

```
Would you like to read a new import file?            ← page title
Choose a PDF, then click Read. Nothing from an
earlier file is shown here.                           ← body
[ drop zone: Import PDF ]
[ Read this PDF ]                                     ← primary
```

Empty on purpose: nothing from a previous dossier is shown. One primary action.
Rejection (`PdfRejected`) shows the short message and a **Back** button.

### 6.2 Reading

Page title, one line saying what is happening, one line saying how long
("This takes about a minute. Do not close this page."), a status block. No
percentage, no streaming of partial results.

### 6.3 Review

```
┌ header ───────────────────────────────────────────────────────────┐
│ [mark] Import file                                [Read another]   │
│        maroc-import-document.pdf · 8 papers read · (Needs a check) │
├ strip ────────────────────────────────────────────────────────────┤
│ Order number [ ]  Exchange rate you enter [ ]  (i)                 │
├───────────────────────────────────────────────────────────────────┤
│ Export:  [Download CSV] [Download JSON]    ← or the override box   │
│ ▌ banner: dossier state in one sentence       [Show passed checks] │
│ ┌ card ┐ ┌ card ┐ ┌ card ┐ ┌ card ┐   summary figures              │
│ ── tab: Broker ── Customs payment • ── Shipping invoice ── …       │
│ ┌ page image (sticky) ────────────┐ ┌ form panel ───────────────┐ │
│ │ ‹  Page 3 · 2 of 2  ›            │ │ COPIED FROM THE PAGE      │ │
│ │                                  │ │ Field | Value | Printed   │ │
│ │                                  │ │ LINES …                   │ │
│ │                                  │ │ YOU TYPE                  │ │
│ │                                  │ │ [ Save ]                  │ │
│ └──────────────────────────────────┘ └───────────────────────────┘ │
│ paper-level banners · Join / Split                                  │
└───────────────────────────────────────────────────────────────────┘
```

Rules for this screen:

- **Reading order is the verification order:** dossier state → which paper →
  that paper's page → its values → what to type → Save. Typing never comes
  before checking.
- **The page image sticks; the fields scroll.** The image is the reference the
  eye returns to. It opens on the page of the first `review` field.
- **Papers are tabs.** A bullet prefix marks a paper that needs a check, so the
  flag is visible without opening it.
- **The form panel is the only elevated surface** besides summary cards, and it
  holds exactly two groups: *Copied from the page* and *You type*. One Save
  commits both.
- **Dossier-level typed values (order number, exchange rate) live in the strip**
  — present, small, out of the way until needed.
- **Unsaved edits survive a tab switch.** Switching papers must not drop a
  value typed or corrected but not yet saved.

---

## 7. Components

Each: what it is, states, the one rule that matters. Class names are in
`app/ui/main.py`. The Streamlit hook is the selector the CSS owns.

| Component | Anatomy | States | Rule |
|---|---|---|---|
| **Banner** `.banner.{good,warn,crit}` | icon + one sentence, tier bg, 4px tier bar, radius-lg | good / warn / crit | One sentence. Count + consequence. Never two banners for the same fact. |
| **Status tag** `.tag.{warn,crit}` | dot + word, radius-sm | warn / crit | Goes after the label it qualifies, inside the row. Always the word. |
| **Status pill** `.status-pill.{good,warn,crit}` | dot + word, fully round | good / warn / crit | Header only: dossier state. |
| **Summary card** `.card` | label · amount · issuer line · optional tag | normal / needs check | Figures only. One card per kind; the paper list remains the full inventory. |
| **Field row** | label (+tag) · value input · printed text | normal / review / edited-unsaved | Printed text is read-only and never reformatted. Value input starts pre-filled with the current value. |
| **Group title** `.group-title` | 12px caps, secondary ink | — | Exactly two per panel. |
| **Form panel** `stForm` | surface, radius-lg, shadow-md, 24px pad | — | One submit. |
| **Button – primary** | accent fill, white label, radius-md | rest / hover / disabled | One primary per view region: `Read this PDF`, `Save`, `Download JSON`. |
| **Button – secondary** | surface fill, hairline, ink label | rest / hover / disabled | Everything else. Ghost is deliberately merged into secondary. |
| **Text input** | surface, hairline, radius-sm, 15/500 | rest / focus / disabled | Focus is the loud state: accent border + 3px halo. |
| **Page nav** | chevron button · `Page N · i of n for this paper` · chevron | first / middle / last (end disabled) | Only when a paper spans >1 page. |
| **Tab** | label, equal width, accent underline | rest / selected | Label = paper name; `•` prefix = needs check. |

New components: build from these first. If a genuinely new one is needed, add it
here with anatomy, states, and a rule before it lands in `main.py`.

---

## 8. Accessibility

Contrast, computed (WCAG relative luminance). Floor: 4.5:1 text, 3:1 for
non-text marks that carry meaning (borders of controls, focus rings, status
dots/bars, icons).

**Passes**

| Pair | Light | Dark |
|---|---|---|
| `ink` on `surface` | 17.7 | 16.1 |
| `ink-secondary` on `surface` | 7.7 | 6.9 |
| white on `accent` | 6.3 | 6.3 |
| `accent-text` on `surface` | 6.3 | 8.9 |
| `good-text` / `warn-text` / `crit-text` on own bg | 6.5 / 6.4 / 6.8 | 8.9 / 9.5 / 6.2 |

**Misses, found while writing this** — none is blocking the job, all are cheap:

| # | Where | Value | Why it matters | Fix |
|---|---|---|---|---|
| A1 | Light `--warn-strong` (#f59e0b) bar/dot on `--warn-bg` | **1.9:1** | The warn banner's left bar and tag dot almost disappear. The word saves it; the shape doesn't. | `--warn-strong` light → `#b45309` (4.5:1) |
| A2 | Dark focus ring: `--accent` on `--surface` | **2.8:1** | Focus is the most-used state in a data-entry tool, and it's under 3:1 in dark. | Dark focus border → `--accent-text` (8.9:1) |
| A3 | Input boundary: `--border` on `--surface` | 1.2:1 | The input is found by its label and halo, not its edge. Accepted in `DESIGN_SYSTEM.md` §8; reconsider for a tool whose whole job is typing into boxes. | Add `--border-strong` for inputs only: light `#8b8b93` (3.4), dark `#71717a` (3.7) |
| A4 | `--ink-muted` placeholder and the `i` glyph | 2.6 light | Placeholder is the only explanation of some boxes. | Use `--ink-secondary` for the strip hint; keep muted for truly redundant cues |
| A5 | Header status pill 11.5px | — | Below the 12px floor, and it carries the dossier state. | 12px |
| A6 | Crit dot on crit bg, light | 3.95 | Passes 3:1; noted so it isn't "fixed" the wrong way. | none |

Other rules:

- **Keyboard:** the form must submit with Enter from any field; tab order
  follows reading order (page nav → fields → Save). Streamlit's focus handling
  is the baseline; don't `tabindex` around it.
- **Targets:** buttons ~40px tall; do not shrink for density.
- **Themes:** light and dark are both first-class and driven by
  `prefers-color-scheme`, with a `[data-theme]` override ready for a toggle.
  Every text color must name the ground it sits on. The start-screen bug in
  `UI_REVIEW.md` §3 (light text on a forced light ground) is the failure mode
  to prevent: whenever you set a ground, set its ink in the same rule.
- **Reduced motion:** nothing animates, nothing to reduce.

---

## 9. Building within Streamlit

The constraints are part of the design. Work with them.

- **All CSS is one `<style>` block at the top of `app/ui/main.py`.** Tokens are
  CSS custom properties declared once; components consume tokens, never hex.
  No second stylesheet, no component library, no React.
- **We override Streamlit's DOM by `data-testid`** (`stBaseButton-primary`,
  `stTextInputRootElement`, `stForm`, `stColumn`, …). `streamlit==1.49.1` is
  pinned. **A Streamlit bump is a design change:** re-check every screen in both
  themes before merging.
- **Use native widgets** (`text_input`, `form`, `tabs`, `columns`, `status`,
  `download_button`) and restyle them. Reach for `unsafe_allow_html` only for
  banners, tags, cards, and the header — and escape every interpolated value
  with `html.escape` if it can originate in a PDF (principle 8).
- **No business logic here** (`AGENTS.md`). The screen calls `app/service.py`.
  Labels, sentences, and ordering come from `app/ui/words.py`. Rules and tiers
  come from validation results; the UI maps severity to tier, nothing more.
- **Two button variants only.** Streamlit exposes `primary` and `secondary`;
  a third would need per-button DOM hacks. Don't invent one.
- **Fonts:** Inter loads from Google Fonts via `@import`. That is a request to an
  external host from a finance tool; see §11.
- **Fake provider is the default.** Design every state to look right with an
  empty or partial dossier — `missing` fields are the normal case there.

---

## 10. Where the repo disagrees with itself

Found while reading the code against the three docs. Real, small, and worth
fixing before building on top.

| # | Finding | Where | Consequence |
|---|---|---|---|
| D1 | **PDF text goes into HTML unescaped.** The summary card's `Issued by {who}` interpolates `supplier_name` (read from the PDF) into a string rendered with `unsafe_allow_html=True`. The filename is escaped; the issuer is not. | `app/ui/main.py` summary cards, `issued_by()` | Violates principle 8 and `AGENTS.md`'s untrusted-documents rule. A crafted issuer name renders as markup. **Fix first.** |
| D2 | **`design/sample.html` is the old language** — cream ground, serif, rail of papers, black primary. The live app is Inter, white/zinc, indigo, tabs. | `design/sample.html` | A new contributor reads the wrong mock. Update it to the current screen or delete it. |
| D3 | **`UI_REVIEW.md` still describes a left paper rail.** The app now uses tabs. | `docs/UI_REVIEW.md` §5 | The "keep the rail" decision was reversed without being recorded. |
| D4 | **`DESIGN_SYSTEM.md` specifies a Ghost button;** the code merged it into secondary and says so. The spec table still lists three. | `docs/DESIGN_SYSTEM.md` §5 | Minor; the status note at the top already explains it. |
| D5 | **Emoji as the brand mark** (`📄` in the header). Renders differently per OS and breaks "no emoji". | `main.py` header | Replace with an inline SVG page glyph in the same tile. |
| D6 | **Export area changes shape with state.** Download buttons are swapped for a checkbox when errors block. | `main.py` export block | Breaks principle 6 (stable places). Keep the buttons, disable them, and put the override beside them. |
| D7 | **Tab-switch persistence is a stated check (`UI_REVIEW.md` §8) with no test.** Fields inside `st.form` keep widget state per key; confirm and cover it. | `main.py` | Risk of silently losing typed values. |
| D8 | `--surface-sunken` equals `--bg` in dark mode, so the header strip has no tone there. | tokens | Cosmetic; give dark a distinct step. |
| D9 | **Not checked live.** This pass read the code and docs and computed contrast; it did not run the app with a real extraction, so spacing in the 2:1 preview/fields split (three sub-columns inside the narrow pane) is unverified. | — | Do a visual pass on a real dossier before changing proportions. |

---

## 11. Open decisions

Each needs an answer from the business or the owner. None blocks the work in §12.

1. **Screen language: English or French?** The papers are French; the SAP GUI
   language is unknown. Argument for French: removes a translation step from
   the most repeated action. Argument against: the code, docs, and prompts are
   English and the team may prefer it. Needs the two accountants.
2. **Self-host Inter, or keep Google Fonts?** `docs/SECURITY.md` is silent about
   the font request. On a locked-down or offline machine the fallback renders
   fine but looks different. Shipping one `.woff2` removes the question.
3. **How should `missing` look?** Today a missing field is a blank input. That
   is honest, but a blank can also mean "forgot to look". Option: a quiet
   `Not on the page` caption in the *Printed text* column. Must never become a
   value, and must never be exported.
4. **Should user-edited values be marked?** The data keeps `method: user` and
   the original. The screen doesn't show it. Option: a small `Edited` marker in
   the row so the clerk can see what they changed before Save/export.
5. **Per-service-line tax and reason codes** on broker invoices are already in
   the UI; whether Phase 1 keeps them document-level is still an open business
   question (`UI_REVIEW.md` §9).

---

## 12. Suggested order of work

Smallest first; each is independently shippable and testable.

1. **D1 — escape PDF text in HTML.** Security-class, ~5 lines, one test.
2. **Token fixes A1, A2, A5** (three one-line changes), and **A3** if the
   owner accepts a heavier input border.
3. **D5, D6, D2** — emoji mark → SVG, stable export area, refresh or delete the
   stale mock.
4. **Decisions 3 and 4** — `missing` and `edited` markers (new, small, high
   value for trust).
5. **Pane proportions** — only after a live look at a real dossier (D9).
6. **Language** — once decision 1 is made; then it is a `words.py` job.

Each change updates this file if it changes a rule, `DESIGN_SYSTEM.md` if it
changes a value, and the screen's tests if it changes behavior.
