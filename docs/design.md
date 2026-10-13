# Design language

How the Import dossier reader looks, sounds, and behaves — and why. This is the
rulebook to check a change against before it ships.

It sits next to documents that already exist:

| Document | Answers | Status |
|---|---|---|
| `docs/UI_REVIEW.md` | What was wrong with the first screen, and the layout it led to | History; the paper rail it describes became tabs (§6.3) |
| `docs/UI_PLAN.md` | How the code is organised, and how it was built, step by step | Done: steps 0 to 7 |
| `design/sample.html` | A picture of the review screen | Generated from the real components and theme; never edit by hand |
| **this file** | Intent, rules, palette, components | Source of truth |

The values live in `app/ui/theme/tokens.css`; this file names what each one is for. If the
two disagree about a *value*, update whichever is stale and the tests in
`tests/unit/test_design_rules.py` will tell you if a rule broke. If they disagree about a
*rule*, this file wins and the code is a bug. §10 lists what was found and what is still open.

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

**Personality: an accountant's desk.** The paper is on the left. The tools are a
ballpoint pen, a highlighter, a red pen, and a ruled ledger. The screen marks
things the way a careful person marks a paper: a highlighter stroke for "look at
this", red ink for "this stops the job", a plain tick for "checked". Everything
else is quiet.

**It is not:** an AI product, and it must not look like one. No sparkle, no
"magic", no assistant voice, no confidence meter — and none of the visual
habits that mark a generated interface (§2, principle 9, and the list in §5.1).

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

3. **Quiet by default; marks mean "look here".**
   `high` has no decoration at all. Only `review`, blocking errors, and the
   dossier state are marked. If most rows are marked, nothing is.
   *Test: squint at a healthy dossier — is the screen almost entirely neutral?*

4. **One thing at a time.**
   One paper open, two groups (copied, typed), one Save per paper, one export
   area. No second place to do the same job.
   *Test: for any action, is there exactly one button for it on screen?*

5. **State is never colour alone.**
   Every status ships a word, and the word sits on a shape (a filled chip or a
   badge with a glyph).
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

9. **Nothing that says "generated".**
   If a screenshot could belong to any SaaS template, it fails. The look comes
   from the job (paper, ledger, pen marks), not from a component-library
   default. The banned list is in §5.1.
   *Test: remove the logo and the copy — is there any detail that is here only
   because it is the usual thing to put there?*

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
- Empty is empty. A totals figure says `Not read` only where a whole figure is
  absent; a field row stays blank.

**Language.** The screen is English today. `UI_REVIEW.md` §7 recommends French
(the papers are French, SAP may be French). That decision is still open — see
§11. Until it is made, write new strings in English and keep them in
`words.py` so the switch is one file.

---

## 4. Status language

The single most important table in this document. Every status in the data maps
to one tier, one word, one mark.

| Tier | Meaning | Word | Mark | Data source |
|---|---|---|---|---|
| **good** | Ready, check passed | `Ready to download` | green chip (header) / tick badge (banner) | no failed validation |
| **review** | Worth a second look, does not block | `Needs a check` | highlighter chip / exclamation badge | field `review`; validation `severity: warning`; boundary `review` |
| **crit** | Blocks the download | `Blocks download` | red chip / cross badge | validation `severity: error`, `status: failed` |
| *(none)* | Read and consistent | — | no decoration | field `high` |
| *(none, see §11)* | Not on the page | — | blank value | field `missing` |

The tier is called **review** in the visual layer (the highlighter), because
that is what it means. Code that still says `warn` maps to it one to one.

Rules:

- **`high` is silent.** It is the normal state; marking it dilutes everything else.
- **Tier follows severity, not volume.** One blocking error makes the dossier
  `crit` regardless of how many `review` items exist.
- **Dossier state is a chip in the header; item state is a chip on the row.**
  Same chip, same words. Never put a banner where a chip will do.
- **A blocked export is overridable by a person, not by the app.** The override
  is an explicit, stored choice (`export_with_errors`).
- **The words don't change between places:** header chip, row chip, and banner
  sentence use the same tier words.

---

## 5. Visual foundations

### 5.1 What this must not look like

These are the habits of generated interfaces. They are banned, not discouraged.
Each has a replacement.

| Banned | Why | Instead |
|---|---|---|
| **A coloured bar on one side of a box** (`border-left: 4px solid …`) | The tell of a generated callout. It also breaks: on a rounded box the bar curves into a **crescent** (seen in the live app on the banner). Never fix it by tweaking the radius — remove the pattern. | A badge with a glyph at the start of the line; text stays ink. |
| **Pastel tint + same-hue dark text** for status | The default "alert" recipe. Low-contrast pairs, and every status looks like every other app's. | Ink text on paper. Colour lives in the badge or chip only. |
| **Indigo / violet accent**, blue-to-purple gradients | The most common generated accent. | Ballpoint blue (§5.2) for actions only. |
| **Slate / zinc / grey-blue neutral scale** | The default Tailwind-style neutrals. | Warm paper neutrals (§5.2). |
| **Inter** (and Roboto, system-ui as the identity) | The default font of generated UIs. | IBM Plex Sans + IBM Plex Mono. |
| **Pill-shaped everything; big soft radii (14–20px)** | Friendly-SaaS shorthand. | Small, firm radii: 3 / 4 / 6px. |
| **Floating cards with drop shadows** | Depth as decoration. | Flat. Rules and ground steps separate things. No shadow tokens exist. |
| **A dot before the label** inside a status chip | Filler. | A filled chip; the fill is the signal. |
| **Emoji or icon-in-a-tinted-square as a logo** | Placeholder branding. | A plain wordmark: the product name in type. |
| **Boxed stat cards in a row** | The dashboard template. | A ruled totals strip (§7). |
| **Gradients, glass, glow, sparkle, illustration** | Decoration with no job. | Nothing. |

When adding anything new, check it against this table first.

### 5.2 Palette — "paper, ink, and three pens"

Names are the job, not the hue. Light is the default; dark is built on purpose,
not inverted. Contrast is WCAG relative luminance, computed (§8).

| Token | Light | Dark | Job |
|---|---|---|---|
| `bg` | `#eeece5` | `#101216` | Page ground (the desk) |
| `surface` | `#fbfaf6` | `#181b21` | Paper: panels, inputs, banners, totals |
| `surface-sunken` | `#e6e3da` | `#0c0e11` | The header strip |
| `rule` | `#d9d5c9` | `#2a2e37` | Hairlines between rows and sections. Decorative |
| `edge` | `#8a8578` | `#7b8394` | Borders of controls (inputs, secondary buttons). 3.5:1 / 4.5:1 |
| `ink` | `#16181d` | `#ecebe6` | Text and values |
| `ink-secondary` | `#4a4d55` | `#a9adb8` | Labels, captions, printed text, placeholders |
| `accent` | `#1f3d8f` | `#3d62c8` | Ballpoint blue: the one action (primary fill, selected tab, focus) |
| `accent-hover` | `#17306f` | `#2f52b0` | Primary hover |
| `accent-text` | `#1f3d8f` | `#9db4f2` | Accent-coloured text on bare ground |
| `on-accent` | `#ffffff` | `#ffffff` | Label on accent fills |
| `review-fill` | `#f2d144` | `#e3c53c` | The highlighter: `Needs a check` chip, badge |
| `on-review` | `#16181d` | `#16181d` | Text/glyph on review fill (11.8:1 / 10.4:1) |
| `review-text` | `#7a5b00` | `#e3c53c` | A review word set on bare ground (rare) |
| `crit-fill` | `#a3231b` | `#e2635a` | The red pen: `Blocks download` chip, badge |
| `on-crit` | `#ffffff` | `#1a0a09` | Text/glyph on crit fill (7.5:1 / 5.7:1) |
| `crit-text` | `#a3231b` | `#e2635a` | A crit word on bare ground |
| `good-fill` | `#2d6a3e` | `#5bb273` | The tick: `Ready to download` chip, badge |
| `on-good` | `#ffffff` | `#08170d` | Text/glyph on good fill (6.5:1 / 7.1:1) |
| `good-text` | `#2d6a3e` | `#5bb273` | A good word on bare ground |

Rules:

- **One action colour.** Ballpoint blue means "you can act here" and "this is
  selected" — nothing else. The three pens mean status — nothing else.
- **Text on a status is always `on-*` on its fill.** Banner and row sentences
  stay in `ink` on `surface`. Status colour is never the colour of a sentence.
- **`review-text` is rare.** Prefer the chip.
- **Dark mode is not an inversion.** Fills are lighter so they hold on a dark
  desk, and their `on-*` text flips to dark where white would fail.

### 5.3 Type

Two families, each with a reason:

- **IBM Plex Sans** — everything the app says and everything the clerk edits.
- **IBM Plex Mono** — the *Printed text* column and nothing else. Mono means
  "this is exactly what the paper said". It is how the eye tells copied from
  typed.

Tabular figures on, globally, so every amount column aligns. No italics.

| Role | Size / line · weight | Family | Used for |
|---|---|---|---|
| Page title | 26 / 32 · 600 · −0.01em | Sans | `st.header` |
| Paper title | 20 / 28 · 600 | Sans | `st.subheader` per paper |
| Figure | 22 / 28 · 600 | Sans | totals strip |
| Body / value | 15 / 22 · 400 (inputs 500) | Sans | inputs, banner sentences, button labels (600) |
| Field label | 14 / 20 · 500 | Sans | row labels |
| Group title | 13 / 18 · 600, sentence case | Sans | `Copied from the page`, `You type`, over a 1px `rule` |
| Caption | 13 / 18 · 400 | Sans | page counts, hints, sub-lines |
| Printed text | 13 / 18 · 400 | **Mono** | the paper's own words |
| Chip | 12 / 16 · 600 | Sans | status chips |

Nothing below 12px. No uppercase tracking-out for labels.

### 5.4 Space, shape, depth

- 4px base; the working range is 16–24 for panel padding and between field
  rows, 4–8 for icon-to-label gaps.
- **Radius is small and firm:** 3px (chips, inputs) · 4px (buttons) · 6px
  (panels, banners). Nothing is a pill.
- **No elevation.** There are no shadow tokens. A panel is a `surface` with a
  1px `rule`; the page is the `bg` around it. In dark the same.
- Lines do the work of structure: a rule under a group title, a rule between
  field rows, a rule between totals — like a ledger.

### 5.5 Icons

Inline SVG, 16×16, 1.75 stroke, round caps, `currentColor`. Four meanings only:
tick (good), exclamation (review), cross (crit), page navigation (chevrons —
Streamlit's Material chevrons). Status icons sit in a **square badge** (20px,
3px radius, filled with the tier's `*-fill`, glyph in `on-*`). No icon font, no
new dependency. An icon is never the only carrier of a meaning (principle 5).

### 5.6 Motion

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
│ Import file                                      [Read another]    │
│ maroc-import-document.pdf · 8 papers read · [Needs a check]        │
├ strip ────────────────────────────────────────────────────────────┤
│ Order number [ ]  Exchange rate you enter [ ]  (not on any page)   │
├───────────────────────────────────────────────────────────────────┤
│ Export:  [Download CSV] [Download JSON]    ← or the override box   │
│ [!] banner: dossier state in one sentence    [Show passed checks]  │
│ ── Supplier invoice ─┬─ Customs value ─┬─ Customs payment ─┬─ … ── │
│  18,921.09 EUR       │ 210,800.00 MAD  │ 44,004.00 MAD     │        │
│  Issued by …         │ Copied from…    │ [Needs a check]   │ totals │
│ ── tab: Broker ── Customs payment • ── Shipping invoice ── …       │
│ ┌ page image (sticky) ────────────┐ ┌ form panel ───────────────┐ │
│ │ ‹  Page 3 · 2 of 2  ›            │ │ Copied from the page ──── │ │
│ │                                  │ │ Field | Value | Printed   │ │
│ │                                  │ │ Lines …                   │ │
│ │                                  │ │ You type ──────────────── │ │
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
- **The form panel holds exactly two groups:** *Copied from the page* and
  *You type*. One Save commits both.
- **Dossier-level typed values (order number, exchange rate) live in the strip**
  — present, small, out of the way until needed.
- **Unsaved edits survive a tab switch.** Switching papers must not drop a
  value typed or corrected but not yet saved.
- **The header is a wordmark, not a logo tile.** The product name in type, the
  file name and count beneath, the dossier chip beside them.

---

## 7. Components

Each: what it is, states, the one rule that matters. The Streamlit hook is the
selector the CSS owns. The class names below are the targets for `main.py`.

| Component | Anatomy | States | Rule |
|---|---|---|---|
| **Banner** | `surface`, 1px `rule`, 6px radius · 20px square badge + one ink sentence | good / review / crit (badge only differs) | One sentence, count + consequence. **No side bar, no tint.** Never two banners for the same fact. |
| **Status chip** | filled `*-fill`, `on-*` word, 3px radius, 12/600 | review / crit / good | Goes after the label it qualifies, or in the header for the dossier. Always the word. No dot. |
| **Totals strip** | one row, up to four cells divided by 1px `rule`; label · figure · sub-line · optional chip | normal / needs check | Figures only, no boxes, no shadow. One cell per kind; the tabs remain the full inventory. |
| **Field row** | label (+chip) · value input · printed text in mono | normal / review / edited-unsaved | Printed text is read-only, mono, never reformatted. The value input starts pre-filled with the current value. |
| **Group title** | 13/600 sentence case over a 1px `rule` | — | Exactly two per panel. |
| **Form panel** | `surface`, 1px `rule`, 6px radius, 24px pad | — | One submit. Flat. |
| **Button – primary** | `accent` fill, `on-accent` label, 4px radius | rest / hover / disabled | One primary per region: `Read this PDF`, `Save`, `Download JSON`. |
| **Button – secondary** | `surface`, 1px `edge`, `ink` label | rest / hover / disabled | Everything else. There is no third variant. |
| **Text input** | `surface`, 1px `edge`, 3px radius, 15/500 | rest / focus / disabled | Focus: border `accent` + 2px solid `accent` outline with 1px offset. |
| **Page nav** | chevron button · `Page N · i of n for this paper` · chevron | first / middle / last (end disabled) | Only when a paper spans more than one page. |
| **Tab** | label, equal width, 2px `accent` underline on selected | rest / selected | Label = paper name; `•` prefix = needs check. |
| **Wordmark** | product name, 20/600, `ink` | — | Plain type. No tile, no emoji. |

New components: build from these first. If a genuinely new one is needed, add it
here with anatomy, states, and a rule — and check §5.1 — before it lands in
`main.py`.

---

## 8. Accessibility

Contrast, computed (WCAG relative luminance). Floor: 4.5:1 text, 3:1 for
non-text marks that carry meaning (control borders, focus rings, icons).

| Pair | Light | Dark |
|---|---|---|
| `ink` on `surface` | 17.0 | 14.5 |
| `ink` on `bg` | 15.0 | 15.7 |
| `ink-secondary` on `surface` / `bg` / `surface-sunken` | 8.1 / 7.2 / 6.6 | 7.7 / 8.4 / 8.6 |
| `on-accent` on `accent` | 9.9 | 5.6 |
| `accent-text` on `surface` / `bg` | 9.5 / 8.4 | 8.4 / 9.2 |
| `on-review` on `review-fill` | 11.8 | 10.4 |
| `on-crit` on `crit-fill` | 7.5 | 5.7 |
| `on-good` on `good-fill` | 6.5 | 7.1 |
| `crit-text` / `good-text` / `review-text` on `surface` | 7.2 / 6.2 / 6.1 | 5.1 / 6.6 / 10.1 |
| `edge` (control border) on `surface` / `bg` | 3.5 / 3.1 | 4.5 / 4.9 |
| Focus ring (`accent` / `accent-text`) on `surface` | 9.5 | 8.4 |

Notes:

- `rule` is decorative (1.3–1.4:1). It never carries meaning on its own; a
  control is found by its `edge` and its label.
- A chip's fill against the paper is not relied on: the word inside the chip is
  the signal and meets the table above.
- The old palette's misses (a 1.9:1 warn bar, a 2.8:1 dark focus ring, 1.2:1
  input edges, 2.6:1 muted ink, an 11.5px pill) are gone by construction. The
  banner bar that caused them is banned (§5.1).
- Status survives greyscale: word on a chip or badge, glyph in the badge.
- **Keyboard:** the form submits with Enter from any field; tab order follows
  reading order (page nav → fields → Save). Don't `tabindex` around Streamlit.
- **Targets:** buttons ~40px tall; do not shrink for density.
- **Themes:** light and dark are both first-class, driven by
  `prefers-color-scheme`, with a `[data-theme]` override ready. Whenever you set
  a ground, set its ink in the same rule — the start-screen bug in
  `UI_REVIEW.md` §3 is what happens otherwise.
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
  banners, chips, the totals strip, and the header — and escape every
  interpolated value with `html.escape` if it can originate in a PDF
  (principle 8).
- **Streamlit's own styling leaks.** Its default theme carries the very look
  §5.1 bans (rounded inputs, grey-blue neutrals). Every widget we show must have
  its ground, ink, border, and radius set by our tokens; a widget we haven't
  restyled is a bug to find, not a default to accept.
- **No business logic here** (`AGENTS.md`). The screen calls `app/service.py`.
  Labels, sentences, and ordering come from `app/ui/words.py`. Rules and tiers
  come from validation results; the UI maps severity to tier, nothing more.
- **Two button variants only.** Streamlit exposes `primary` and `secondary`;
  a third would need per-button DOM hacks. Don't invent one.
- **Fonts:** IBM Plex Sans and Mono ship in the repo (`app/ui/static/fonts`, SIL OFL
  license) and are served by Streamlit's static folder, so the screen makes no request to an
  outside host. That needs `--server.enableStaticServing true` in the run command; without it
  the screen falls back to system fonts. `--server.maxUploadSize 30` makes the upload box state
  the real limit.
- **Fake provider is the default.** Design every state to look right with an
  empty or partial dossier — `missing` fields are the normal case there.

---

## 10. Where the repo disagrees with itself

Found while reading the code against the docs, and from a screenshot of the
live app. Real, small, and worth fixing before building on top.

**Status after step 7 of `docs/UI_PLAN.md`**

| Finding | Status |
|---|---|
| D1 PDF text unescaped | **Fixed** (step 1), and guarded by tests |
| D2 crescent, D3 generated skin | **Fixed** (step 5) |
| D4 stale mock | **Fixed** (step 7): `design/sample.html` is generated from the real parts |
| D5 UI_REVIEW describes a rail | **Noted** (step 7): a note at the top of that file |
| D6 export area changes shape | **Open**: a behaviour change, not yet decided |
| D7 unsaved values across papers | **Settled** (step 3): they survive, and the key names are pinned by a test |
| D8 not checked live | **Partly**: wider form (5:6) done; a look at a real dossier is still owed |
| D9 header ignores flagged values | **Fixed** (step 7): a value in `review` now makes the dossier `warn` |

| # | Finding | Where | Consequence |
|---|---|---|---|
| D1 | **PDF text goes into HTML unescaped.** The summary card's `Issued by {who}` interpolates `supplier_name` (read from the PDF) into a string rendered with `unsafe_allow_html=True`. The filename is escaped; the issuer is not. | `app/ui/main.py` summary cards, `issued_by()` | Violates principle 8 and `AGENTS.md`'s untrusted-documents rule. A crafted issuer name renders as markup. **Fix first.** |
| D2 | **The banner draws a crescent.** `border-left: 4px solid` on a box with `border-radius: 20px` makes the bar follow the corner. | `.banner` in `main.py` | Visible defect, and the generated-callout look §5.1 bans. Remove the bar; don't re-round it. |
| D3 | **The whole skin is the generated default** — Inter, indigo, zinc neutrals, pastel-tint status, soft shadowed cards, pill status, dotted tags, emoji brand mark. | `main.py` CSS; `DESIGN_SYSTEM.md` | Replace with §5 and §7 in one pass. |
| D4 | **`design/sample.html` was an older, third look** — cream ground, serif, rail of papers, black primary. | `design/sample.html` | A new contributor reads the wrong mock. Now generated; see the status table. |
| D5 | **`UI_REVIEW.md` still describes a left paper rail.** The app now uses tabs. | `docs/UI_REVIEW.md` §5 | The "keep the rail" decision was reversed without being recorded. |
| D6 | **Export area changes shape with state.** Download buttons are swapped for a checkbox when errors block. | `main.py` export block | Breaks principle 6. Keep the buttons, disable them, put the override beside them. |
| D7 | **Tab-switch persistence is a stated check (`UI_REVIEW.md` §8) with no test.** | `main.py` | Risk of silently losing typed values. |
| D9 | **The dossier chip ignored fields that need a check.** `dossier_tier` looked only at validation results, so a dossier whose fields were flagged `review` but whose checks passed showed `Ready to download` next to `Needs a check` chips. Section 4 says a field in `review` makes the tier `warn`. | `app/ui/view.py` `dossier_tier` | Fixed: the tier is `warn` when any value is in `review`; with no failed checks the banner counts values (`3 value(s) might need a second look…`). |
| D8 | **Not checked live beyond one screenshot.** Spacing in the 2:1 preview/fields split (three sub-columns inside the narrow pane) is unverified on a real dossier. | — | Do a visual pass on a real dossier before changing proportions. |

---

## 11. Open decisions

Each needs an answer from the business or the owner. None blocks the work in §12.

1. **Screen language: English or French?** The papers are French; the SAP GUI
   language is unknown. For French: removes a translation step from the most
   repeated action. Against: the code, docs, and prompts are English. Needs the
   two accountants.
2. ~~Self-host the fonts, or keep Google Fonts?~~ **Decided: in the repo** (step 1).
3. **How should `missing` look?** Today a missing field is a blank input —
   honest, but a blank can also mean "forgot to look". Option: a quiet
   `Not on the page` caption in the *Printed text* column. It must never become
   a value and must never be exported.
4. **Should user-edited values be marked?** The data keeps `method: user` and
   the original. The screen doesn't show it. Option: a small `Edited` marker in
   the row so the clerk sees what they changed before Save/export.
5. **Per-service-line tax and reason codes** on broker invoices are already in
   the UI; whether Phase 1 keeps them document-level is still an open business
   question (`UI_REVIEW.md` §9).

---

## 12. Suggested order of work

Smallest first; each is independently shippable and testable. Items 1 to 3 are done
(`docs/UI_PLAN.md` sections 14 to 20); items 4 to 6 are still open.

1. **D1 — escape PDF text in HTML.** Security-class, ~5 lines, one test.
2. **D2 + D3 — the new skin, in one pass.** Tokens (§5.2), fonts (§5.3),
   banner without a bar (§7), chips instead of tags and pills, flat panel,
   ruled totals strip instead of cards, wordmark instead of the emoji tile,
   small radii, input `edge` and focus. One PR, checked live in both themes,
   with a before/after screenshot.
3. **D6** — stable export area (open); **D4** — the stale mock (done, step 7).
4. **Decisions 3 and 4** — `missing` and `edited` markers (new, small, high
   value for trust).
5. **Pane proportions** — only after a live look at a real dossier (D8).
6. **Language** — once decision 1 is made; then it is a `words.py` job.

Each change updates this file if it changes a rule or a value, and the screen's
tests if it changes behavior.
