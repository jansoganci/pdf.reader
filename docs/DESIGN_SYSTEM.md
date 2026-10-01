# Design system — visual language for the review screen

This is the visual redesign that follows `docs/UI_REVIEW.md`. That document
fixed *what's on the screen and where* (one paper at a time, its page beside
two groups, one Save, one export). This document fixes *what it looks like*:
type, color, spacing, and the style of every button, box, and tag. It does
not reopen the layout — list on the left, image beside two groups, one Save
— that work is done and stays.

Every color below was checked with the WCAG contrast formula, not chosen by
eye. The numbers are in §8. Where a choice doesn't clear the usual bar, that's
called out instead of hidden.

**Status: implemented in `app/ui/main.py`**, in the five phases below, each
checked live in both themes before moving to the next.

1. Foundation — Inter, the full token set, base background/ink, heading sizes.
2. Banners & tags — the warn/crit split landed (§9's first question: yes).
3. Buttons & inputs — full ownership of Streamlit's native widget chrome.
4. Cards & spacing — summary tiles and the two-group panel as real cards.
5. Icons & page nav — chevron icons replace `◀`/`▶`; status icons on banners.

Two deviations from the spec above, found during implementation, not before:

- **"Ghost" buttons were merged into "secondary."** Streamlit's button API
  only exposes `primary`/`secondary` as a `type`; a third visual variant
  would need per-button DOM targeting hacks to fake. Every non-primary
  button (Show/Hide passed checks, Join/Split, Read another file) renders
  as secondary instead.
- **An extra selector was needed for text inputs.** Streamlit nests an
  unnamed `<div>` inside `stTextInputRootElement` that carries its own dark
  fill independent of the root's background — both had to be targeted for
  the input box to actually turn white in light mode, not just its border.

## 1. Direction, decided

Four calls, made before any hex was picked:

| Question | Decision |
|---|---|
| Aesthetic | Modern SaaS — soft shadows, rounded cards, generous whitespace, Inter |
| Palette | A new neutral palette, built for this screen, not the current cream/amber and not a client brand kit |
| Density | Comfortable — room to breathe over a 20–35 minute file, not maximum rows-per-screen |
| Theme | Both light and dark, built and checked on purpose — not just "don't break dark mode" |

## 2. Typeface

**Inter**, loaded once via Google Fonts, falling back to the system sans if
the font fails to load:

```css
font-family: "Inter", -apple-system, "Segoe UI", sans-serif;
```

Inter was built for UI text at small sizes — it's what the "Modern SaaS"
reference points (Linear, Notion, Stripe) mostly use, it has a real weight
range (400–700), and it ships with `tabular-nums` figures, which this screen
needs: every money column should line up.

Money and page-count figures get `font-variant-numeric: tabular-nums`
specifically — labels and prose stay proportional.

### Type scale

Comfortable density means fewer, larger steps rather than a dense ladder:

| Role | Size / line | Weight | Color | Used for |
|---|---|---|---|---|
| Page title | 26px / 32px | 700 | ink | "Import file" |
| Paper title | 20px / 28px | 600 | ink | "Broker invoice" subheader |
| Group label | 12px / 16px, uppercase, +0.06em | 600 | ink-secondary | "COPIED FROM THE PAGE" / "YOU TYPE" |
| Field label | 14px / 20px | 500 | ink | "Issued by", "Total", input labels |
| Body / value | 15px / 22px | 500 | ink | table values, button labels, typed text |
| Caption / meta | 13px / 18px | 400 | ink-secondary | page counts, "Issued by…", printed-text column |

No serif anywhere, no italics — one family, weight does the work.

## 3. Color tokens

Defined as CSS custom properties so light/dark is one variable swap, not a
second stylesheet. Base block is light; dark overrides both on the OS
`prefers-color-scheme` and on a `data-theme` attribute, so a manual toggle
can be wired in later without touching a single color value elsewhere.

```css
:root {
  --bg:            #fafafa;
  --surface:       #ffffff;
  --surface-sunken:#f4f4f5;
  --border:        #e4e4e7;

  --ink:           #18181b;
  --ink-secondary: #52525b;
  --ink-muted:     #a1a1aa;  /* decorative only — see §8 */

  --accent:        #4f46e5;
  --accent-hover:  #4338ca;
  --accent-text:   #4f46e5;
  --accent-soft:   #eef2ff;

  --good-text: #166534; --good-bg: #dcfce7; --good-strong: #16a34a;
  --warn-text: #92400e; --warn-bg: #fef3c7; --warn-strong: #f59e0b;
  --crit-text: #991b1b; --crit-bg: #fee2e2; --crit-strong: #dc2626;
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { /* ...dark block below... */ }
}
:root[data-theme="dark"] { /* ...same dark block... */ }
```

Dark block (identical under both selectors above):

```css
--bg:            #0f0f12;
--surface:       #18181b;
--surface-sunken:#0f0f12;
--border:        #2a2a2e;

--ink:           #f4f4f5;
--ink-secondary: #a1a1aa;
--ink-muted:     #71717a;

--accent:        #4f46e5;   /* same hex both themes — always paired with white text */
--accent-hover:  #4338ca;
--accent-text:   #a5b4fc;   /* lighter, for text/links directly on the dark surface */
--accent-soft:   #1e1b4b;

--good-text: #4ade80; --good-bg: #14281d; --good-strong: #22c55e;
--warn-text: #fbbf24; --warn-bg: #2b2111; --warn-strong: #f59e0b;
--crit-text: #f87171; --crit-bg: #2c1515; --crit-strong: #ef4444;
```

The accent is the **same hex in both themes** on purpose: `#4f46e5` clears
white-text contrast on its own in both (6.3:1), so there's one indigo, not
two, and buttons don't shift hue when the OS theme flips. Only the
*text-on-bare-background* variant (`--accent-text`, for inline links) needs
its own lighter dark-mode step, because indigo-on-dark-gray is a different
contrast problem than white-on-indigo.

### The three status colors, and a fourth tier this screen doesn't have yet

`good` / `warn` / `crit` map onto the data model that's already there:

- **good** — dossier ready to export, a check passed.
- **warn** — a field is `review` status; a non-blocking validation `warning`.
- **crit** — a blocking validation `error` (`severity: "error"` in
  `app/validation/rules.py`).

Today the screen only has two tiers in practice: the amber banner covers
*both* "something's worth a second look" and "this blocks the download,"
with identical color and wording. Introducing `crit` properly — a red
banner specifically for blocking errors, amber reserved for non-blocking
review items — is a real, if small, behavior change, not pure restyling.
It's flagged in §9 rather than assumed.

## 4. Spacing, radius, elevation

**Spacing** — 4px base unit: `4 · 8 · 12 · 16 · 20 · 24 · 32 · 40 · 48`.
Comfortable density leans on the 16–24 range for card padding and the gap
between a field's rows; 4–8 stays for tight internal gaps (icon-to-label).

**Radius** — a small scale, not one flat number, so bigger things look
softer than small controls:

| Token | Value | Used for |
|---|---|---|
| `--radius-sm` | 10px | tags, inputs |
| `--radius-md` | 14px | buttons |
| `--radius-lg` | 20px | cards, the summary tiles, the two-group panel |

**Elevation** — shadows in light mode, a lighter surface + hairline border
in dark mode (a shadow on a near-black background doesn't read; a lighter
panel does):

| Token | Light | Dark |
|---|---|---|
| `--shadow-sm` | `0 1px 3px rgba(16,24,40,.08), 0 1px 2px rgba(16,24,40,.04)` | none — `1px solid var(--border)` instead |
| `--shadow-md` | `0 4px 12px rgba(16,24,40,.08), 0 2px 4px rgba(16,24,40,.04)` | none — `1px solid var(--border)`, `--surface` one step lighter than `--bg` |

## 5. Components

**Buttons**

| Variant | Background | Text | Border | Used for |
|---|---|---|---|---|
| Primary | `--accent`, hover `--accent-hover` | white | none | Save, Read this PDF, selected paper in the list |
| Secondary | `--surface` | `--ink` | `1px solid var(--border)` | Read another file, unselected paper, page nav |
| Ghost | transparent | `--accent-text` | none | Show/Hide passed checks, Join/Split |

All three: `--radius-md`, 15px/600 weight label, 10px/18px padding (comfortable
touch target, ~40px tall), `--shadow-sm` on primary only. Disabled state:
50% opacity, no hover change.

**Text inputs** — `--surface` background, `1px solid var(--border)`,
`--radius-sm`, 10px/14px padding, 15px/500 text in `--ink`. Resting border
is deliberately light (see §8's note on this) — the control that actually
needs to be unmistakable is the **focus ring**: `border-color: var(--accent)`
plus `box-shadow: 0 0 0 3px rgba(79,70,229,.35)`, same in both themes.

**Status tag** (the "Needs a check" pill) — `--radius-sm`, `{tier}-bg`
background, `{tier}-text` label, a small 6px dot in `{tier}-strong` before
the text. Never color alone: the word ("Needs a check") always ships with
the pill, same as today.

**Banner** — full-width, `--radius-lg`, `{tier}-bg`/`{tier}-text`, a left
accent bar in `{tier}-strong` (4px), an icon (see below) before the message.

**Cards** (summary tiles, paper-list items, the two-group panel) —
`--surface`, `--radius-lg`, `--shadow-sm` at rest. The two-group panel
(the form) steps up to `--shadow-md` since it's the thing being worked on.
Selected paper in the list: `--accent` fill + white text, same shape as
primary button, not a separate style.

**Group header** ("Copied from the page" / "You type") — type-scale "Group
label" row above a `1px solid var(--border)` rule, 12px gap below before the
first field row.

**Field row** — label / editable value / printed text in three columns, each
row separated by a `1px solid var(--border)` hairline, 12px vertical padding
(comfortable, not the previous tight packing).

**Page nav** — replace the `◀`/`▶` unicode glyphs (render inconsistently
across fonts and platforms) with the chevron icons below, in ghost buttons.

**Icons** — one small inline-SVG set, stroke-based, 1.5px stroke, rounded
caps, `currentColor` fill so they inherit whatever text color they sit in (no
icon font, no new dependency — consistent with AGENTS.md's "don't add a
dependency without a reason"). Four icons cover everything on this screen:
check-circle (good), alert-triangle (warn), alert-octagon (crit),
chevron-left/chevron-right (page nav). Lucide's icon set is the visual
reference if exact paths are wanted later — same stroke style, MIT-licensed.

## 6. What's not changing

- The structure from `docs/UI_REVIEW.md`: paper list on the left, page image
  beside exactly two groups, one Save per paper, one export area.
- Streamlit only, no React/custom frontend, no new routes — this is still
  one file's CSS and component choices.
- Screen labels stay English (per the prior task); this document is colors
  and shapes, not copy.
- The service boundary: Streamlit still only calls `app/service.py`; no
  business rules move into this layer.

## 7. Migrating the current CSS

What's in `app/ui/main.py` today, and its replacement token:

| Current hardcoded value | Replace with |
|---|---|
| `.stApp { background: #f4f1ea; color: #1c1915; }` | `background: var(--bg); color: var(--ink);` |
| `.banner.warn { background:#f8ecd8; color:#8a5a12; }` | `--warn-bg` / `--warn-text` |
| `.banner.ok { background:#e5f4eb; color:#1f6b45; }` | `--good-bg` / `--good-text` |
| `.tag { background:#f8ecd8; color:#8a5a12; }` | tier-specific — most tags today are `warn`, but a blocking one should use `crit` once §9's banner split lands |
| `div[data-testid="stCaptionContainer"] { color:#6b645b; }` | `var(--ink-secondary)` |
| `.group-title { color:#6b645b; }` | `var(--ink-secondary)` (same token, now named) |

## 8. Accessibility notes — the computed numbers

Every pair below is the WCAG relative-luminance contrast ratio, not an
estimate. ≥4.5:1 is the bar for normal text; ≥3:1 is the floor for large
text and non-text UI boundaries.

| Pair | Ratio | Verdict |
|---|---|---|
| Light ink on page / card | 17.0 / 17.7 | pass |
| Light secondary ink on card | 7.7 | pass |
| Light muted ink on card | 2.6 | **below 3:1 — decorative only, never the only carrier of a value** |
| White text on accent / accent-hover | 6.3 / 7.9 | pass |
| Light good/warn/crit text on their tint | 6.5 / 6.4 / 6.8 | pass |
| Dark ink on page / card | 17.4 / 16.1 | pass |
| Dark secondary ink on card | 6.9 | pass |
| Dark muted ink on card | 3.7 | pass (large text / UI only) |
| Dark accent-text on card | 8.9 | pass |
| Dark good/warn/crit text on their tint | 8.9 / 9.5 / 6.2 | pass |

**The one real trade-off:** `--border` (`#e4e4e7` light / `#2a2a2e` dark)
sits around 1.3:1 against its surface — well under the 3:1 non-text floor.
That's deliberate, not an oversight: every modern reference point for this
aesthetic (Linear, Notion, Stripe, GitHub's own forms) uses a near-invisible
resting border and puts the real accessibility weight on the **focus ring**
(§5), which clears contrast cleanly, plus the fact that every input here
sits directly under its own visible label — the control is never identified
by its border alone. If that trade-off is wrong for this audience, the fix
is a single token change (`--border` → the `#8b8b93`-class gray, 3.4:1,
tested and ready), traded against a visibly heavier, more utilitarian look.

`--ink-muted` is scoped the same way: it's for a hint that's redundant with
something already visible (e.g. a disabled control), never for a value the
clerk needs to read to do the job. Anything load-bearing uses `--ink` or
`--ink-secondary`, both of which clear 4.5:1 in both themes.

## 9. Open questions

Two of the original four are settled — split the banner: done; implement now:
done. Two are still genuinely open, and nothing above is blocked on them:

- **Any existing Voxus Systems brand color I should know about?** "New
  neutral palette" was the explicit choice over "match brand" — confirming
  there's no internal style guide this should have matched instead.
- **Inter from Google Fonts — confirmed fine, or does it need to be
  self-hosted?** Still loaded via `@import`, assuming normal internet access
  on these two machines. If they're locked down or offline, swap the
  `@import` for a shipped `.woff2` — one line, no token changes.
