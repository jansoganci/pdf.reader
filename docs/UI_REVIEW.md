# UI review — the review screen, not the model

This reviews `app/ui/main.py` and `app/ui/words.py` as they run today at
`http://127.0.0.1:8765`, against `design/sample.html` and against the real
extraction already sitting in `data/app.sqlite` for
`maroc-import-document.pdf`. Every field value quoted below is the actual
cached extraction for that file, not a guess. Sources used: the crosstab.io
Streamlit review, the Kanaries `st.dataframe`/`st.data_editor` guide, and the
data-entry-panel article listed in the task — cited inline where used.

## 1. The job

Two accountants take a PDF pack from a customs broker — one scan, no text
layer, about ten pages holding six to eight different papers — and read it
into SAP by hand through ZMM073, FB01, FB60, and MIRO. 50–80 packs a month,
20–35 minutes each. This screen does one narrow part of that: show what was
read off each paper, let the person fix a misread value, let them type the
handful of things SAP needs that no paper prints, and hand them a JSON and a
CSV. It does not post anything and it does not decide accounting treatment.

## 2. What the person must see in the first ten seconds

Which papers were found (a broker invoice, a two-page customs liquidation,
two ONCF invoices, a two-page Maersk invoice, a DUM, a foreign invoice, a
licence — eight items here), whether anything needs a second look before they
trust it, and the first flagged paper already open with its page and its
fields side by side. Nothing should ask them to type before they've verified
anything is correct — typing SAP-only fields is the last step of this job,
not the first thing on screen.

## 3. The current screen, top to bottom

**Start screen (`st.file_uploader`, `st.header`, `st.button`, lines 30–164).**
Verified live: with the OS/browser in dark mode — `prefers-color-scheme:
dark` — the heading, the caption, and the "Import PDF" label render as
`rgb(250, 250, 250)` text (Streamlit's default dark-theme foreground) on the
`#f4f1ea` cream background the app forces with custom CSS (`main.py:37`).
That is white-on-off-white: the heading and instructions are functionally
invisible; only the dark file-drop box and the red button survive, and
there's nothing to explain why the rest of the screen looks blank. The
custom CSS sets a background color and never pins a text color to go with
it, so it inherits whatever theme the browser resolves to. This is the very
first thing either accountant sees.

**Header row (`head_left`/`head_right` columns, lines 174–195).** Filename
and status caption on the left; on the right, four buttons and a checkbox
sharing one row: "Read another file", "Download CSV", "Download JSON", and —
only when there are blocking errors — a "Download anyway" checkbox that pops
into that same row and shifts the download buttons' position. A row whose
contents rearrange itself based on data state is exactly the kind of
"stable action locations, no layout shifts" violation the data-entry-panel
guidance warns against.

**"Not on the PDF" file form (`st.form("file-manual")`, lines 197–204).**
Two text boxes — Order number, Exchange rate you enter — sit above the
banner, above the summary cards, above a single paper's fields, before the
person has looked at one page of the PDF. These two values come from a
different system entirely (ZMM073, Bank Al-Maghrib) and apply once per
dossier, not per paper, yet they're the first data-entry the screen offers.

**Banner + "Show/Hide passed checks" (lines 206–212).** One colored div,
plain text, one button. This part works; see §4.

**Summary cards (lines 214–239).** Four `st.columns` cards for supplier
invoice, customs value, customs payment, shipping invoice. Useful, but it
duplicates the amounts the paper list already shows one section down, and it
picks at most one document per kind — a file with two ONCF logistics
invoices only ever shows one logistics figure here.

**Paper list (`list_column`, lines 242–261).** One full-width `st.button`
per document plus a caption line underneath. This is the one part of the
screen that does its job cleanly: eight rows, each showing pages, issuer,
and headline amount, is a real 3-second scan of what's in the pack.

**Detail pane (`detail_column`, lines 264–338) — this is most of the screen
and most of the problem:**

- *Preview* (`preview` column, lines 269–276): `page_image()` renders only
  `document.page_numbers[0]` — the paper's *first* page. Verified against
  the cached data: the customs liquidation spans pages 2–3, and its
  `total_amount` — the one field flagged `review` on that paper — was read
  from **page 3**. The Maersk invoice spans pages 6–7 with every field read
  from page 6, so that case happens to be fine, but the liquidation case
  shows the fault directly: the one field the clerk most needs to check
  against the paper sits on a page this screen never displays. There is no
  page-forward control at all.
- *Field table* (`fields` column, lines 277–291): four `st.columns` per row
  (Field / Value / Printed text / Correct), 7–13 rows depending on the
  paper (13 for the customs declaration). Clicking "Correct" only sets
  `st.session_state["editing"]`; it doesn't open anything on that row.
- *Lines* (lines 292–299): plain numbered `st.write` text, not a table —
  fine for 3–7 lines, but it's one more visually distinct block between the
  field table and the manual form.
- *Paper manual form* (`st.form(f"paper-manual-{document.id}")`, lines
  300–312): five more text boxes — vendor code, posting date, tax code,
  reason code, G/L account — plus a sixth, SAP reference, for customs
  papers. A second "Save" button, visually identical to the first one at
  the top of the page.
- *The correction box* (lines 313–319): this is where "Correct" actually
  lands — a single unlabeled-by-position `st.text_input` rendered **after**
  the field table, after the lines, after the entire manual form. Clicking
  "Correct" on the first field of a 13-row customs-declaration table sends
  the eye and the mouse past that table, past its lines, past six more text
  boxes, to a box at the bottom of the pane. And the box starts **empty** —
  it is never given `value=`, so fixing one digit in a mostly-correct amount
  means retyping the whole value from memory or from the "Printed text"
  column three sections up.

Counted precisely: there are **three** separate save actions on this screen
per open paper (file-form Save, paper-form Save, Save correction), not two.

**Validation banners, passed-check captions, Join/Split controls (lines
321–338).** Correctly scoped to the open paper; not sequenced ahead of the
data-entry blocks, which is right.

## 4. What to keep

- The paper list on the left: name, pages, issuer, amount, one glance.
- Page image and that paper's fields in the same view, side by side — the
  right shape for "look at the paper, look at the value." It just needs to
  cover every page of a multi-page paper, not only the first.
- The Field / Value / Printed-text column shape. Comparing the read value
  against the raw printed text in place is the actual verification act this
  screen exists for.
- `high` / `review` / `missing` as a plain tag, never a percentage.
- The amber/green banner as a single-glance dossier state.
- Validation sentences tied to a named paper ("Shipping invoice: the lines
  on the page do not add up…") rather than a bare rule id.
- Join/Split for wrong page grouping — needs to stay somewhere on this
  screen, just not fighting for space with everything else.

`design/sample.html` did not fail the live screen and the live screen did
not fail it — they agree on the shape (list + image + table) almost exactly.
Where they part ways is the parts the mock leaves out entirely: it has no
"Not on the PDF" boxes anywhere, no correction workflow, no second Save. The
mock is a plausible *read-only* screen; it was never a complete mock of this
job, because the job is at least as much about the typed SAP fields as the
copied ones, and the mock shows none of that weight.

## 5. The recommended screen

One file, `app/ui/main.py`, same as now. Left rail unchanged: one row per
paper. Right side, for the open paper: the page image stays visible next to
exactly two groups, nothing else between them:

**Copied from the page** — every field read off this paper plus its line
items, value shown next to its printed text, corrected in place (see §7 on
`st.data_editor`), no separate button, no detached box.

**You type** — the handful of SAP-only fields for this paper, in the same
pane, same visual weight as the copied group, not a form bolted on
afterward.

One Save commits both groups for the open paper together. One export area
(still both CSV and JSON — that's a file-format choice, not two actions)
replaces the buttons currently mixed into the header row.

The two dossier-level typed values (order number, exchange rate you enter)
don't belong to any one paper, so they don't fit either group — keep them,
but as a small fixed strip near the header, not as the first full form on
the page.

Concretely, using this file's own extracted data:

| Paper | Copied from the page | You type |
|---|---|---|
| Supplier invoice (Ekom Eczacıbaşı Dış Tic. A.Ş.) | Issued by, invoice number `EX/26/502459/1`, date, currency EUR, net/total 18,921.09, FOB 16,696.43, freight 2,224.66, package count, 2 product lines | Vendor code, posting date, tax code, reason code, G/L account |
| Maersk invoice | Issued by, invoice number `7631239091`, date, currency MAD, net 6,464.00, tax 332.80, total 6,796.80 (flagged), bill of lading, containers, 5 charge lines | Same five |
| Transit Trust broker invoice | Issued by, invoice number `2026/003654`, date, net 5,180.00, tax 786.00, total 6,830.00 (flagged — lines sum to 6,044, not 6,830), 7 service lines (Honoraire, Ouverture dossier, Manipulation, Imprimés, Lettre de réserve, Transport, Magasinage) | Same five, at document level (see §9 — the real process assigns a different tax/reason code per service line) |
| Customs liquidation | Payment number `300001CEE20260001924`, payment date 07/09/2026, customs value 210,800.00, tax 42,793.00, total 44,004.00 (flagged, printed on page 3), HS code, package count, regime, 3 duty lines | Same five, plus SAP reference (stays empty) |

## 6. What not to add

No confidence percentage. No SAP posting, matching, or credentials. No GL,
tax-code, or reason-code mapping table. No per-line tax/reason-code fields
until §9 is answered. No batch upload of multiple PDFs. No new page, tab, or
route — one file, one screen. No theme toggle — just give the existing theme
an explicit text color so it survives whatever the browser resolves to.

## 7. Ranked changes, and what each buys back from the 30 minutes

1. **Show the page the flagged field actually came from**, with a way to
   step to the paper's other pages, not just page one. Verified gap: the
   liquidation's own flagged total sits on page 3 of a 3-page pane that only
   ever shows page 2. ~5 minutes a file — this is the one check the whole
   screen exists to support, and right now it can't be done without leaving
   the app.
2. **Correct the value in place, pre-filled with the current text**, instead
   of an empty box below the table, the lines, and six more inputs.
   ~2–3 minutes a file across a handful of corrections.
3. **One Save per paper**, both groups together, instead of three separate
   save actions scattered top, middle, and bottom of the pane. ~2 minutes a
   file in fewer places to remember to click.
4. **Fix the white-on-cream text on the start screen.** Not present on every
   machine — only where the OS/browser resolves to dark mode — but when it
   hits, the opening screen is unreadable. Call it 1 minute on average,
   much more on an affected machine.
5. **Move the two dossier-level typed boxes** out of the top of the page —
   before any paper is open — into a small fixed strip. ~1 minute a file in
   not scrolling past two irrelevant inputs to reach the actual review.
6. **One export area**, not buttons sharing a row with a checkbox that
   appears and shifts them. ~30 seconds a file.
7. **Move the screen's labels to French** (see below). Each of the ~9–13
   field comparisons on each of 6–8 papers is a glance at a French word on
   the page and an English word on screen; a few seconds each, an estimate
   of ~2 minutes a file in total, not a timed measurement.

**Language.** The papers are French — *N° et date liquidation*, *Crédit
d'enlèvement*, *Honoraire*, *Ouverture dossier* are the actual printed
terms in this sample. The two people using this screen work these French
papers into a Moroccan SAP entity every day; matching the screen to the
paper in front of them removes a small translation step from every single
field check, which is the single most repeated action in the job. Recommend
French for the screen's own labels. This doesn't touch the app: the code,
comments, and this document stay in English.

**On `st.data_editor` for in-place correction.** Per the Kanaries guide, an
editable table returns the edited grid to the script on interaction but has
no native per-row action button and no per-cell callback — there's no way
to "auto-save as you type." That's fine here: read the returned frame back
against the original only when the one Save button fires, which is the
design in §5 anyway. What it does cost: the current code renders each field
as four independent `st.columns`, which is easy to reason about one row at a
time; a `data_editor` table is one call over a whole dataframe, so pulling
"printed text" in as a read-only companion column and mapping edited cells
back to `correct_field()` calls is a real rewrite of that block, not a
one-line swap. And per the crosstab.io review, Streamlit gives you columns
and a sidebar and no custom callbacks, so making the page image visually
"stick" while the field list is scrolled needs hand-written CSS against
Streamlit's own internal class names — which already happens in this file
today (`main.py:31-49`) and is not guaranteed stable across a Streamlit
version bump.

## 8. Checks the next build must pass

- A clerk can correct one copied amount and type one empty SAP field for the
  same paper without hunting for either box.
- A field that isn't on the PDF renders and exports as empty — never a
  zero, a guess, or a placeholder.
- The page image shown is a page this paper actually spans, and every page
  the paper spans is reachable from the same pane — not only page one.
- Switching to a different paper and back doesn't drop a value already typed
  or corrected but not yet saved.
- CSV and JSON export still produce, and a dossier with unacknowledged
  errors still blocks export until the person explicitly allows it.
- Status is only `high`, `review`, or `missing` — never a percentage.

## 9. Questions for the business — short, non-blocking

- Transit Trust service lines each carry their own tax code and reason code
  in the real SAP entry (Honoraire → GK/JE, Transport → IN/JC, and so on,
  per `Import Docs Entry Process.docx`). This screen currently offers one
  tax code and one reason code per document. Does Phase 1 stay
  document-level, or does the broker invoice need one row of "you type"
  fields per service line?
- Confirm French is right for both accountants, and check whether the SAP
  GUI itself is configured in French or English for them — matching the
  paper is only half the comparison; the SAP screen they type into is the
  other half.
- Do the two dossier-level fields (order number, exchange rate you enter)
  belong on this screen at all, given the order number comes from a
  separate ZMM073 lookup and the exchange rate from Bank Al-Maghrib — or is
  this screen just holding a place for values entered somewhere else?
- What OS/browser setup do the two accountants actually run — the theme bug
  in §3 only shows up when the system resolves to dark mode.
