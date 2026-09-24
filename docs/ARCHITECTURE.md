# Architecture

Phase 1 helps Finance read one import dossier. It does not post to SAP and it does not choose accounting treatment.

## Pipeline

```text
Streamlit
→ application service
→ PDF preprocessing
→ page classification
→ document boundary detection
→ document grouping
→ document-specific extraction
→ normalization
→ deterministic validation
→ human review
→ SQLite and local files
→ JSON / CSV export
```

Streamlit collects the file, shows documents and fields, accepts corrections, and offers export. It does not classify, extract, normalize, validate, or store rules.

The application service is the only door into the pipeline. FastAPI is not part of Phase 1. If a later deployment needs an API, it calls this same service.

## What Phase 1 does not include

- FastAPI or any other HTTP service
- SAP posting, matching, or credentials
- GL accounts, tax codes, reason codes, and account 159220010
- Queues, workers, microservices, and workflow engines
- PostgreSQL
- A separate OCR product, unless a later test shows the multimodal reader is not enough
- A numeric confidence score from the model

## Project layout

```text
app/
  ui/                 # Streamlit only
  service.py          # the door Streamlit calls
  pipeline/
  pdf/
  documents/          # one folder per document type, plus registry
  extraction/
  providers/
  validation/
  review/
  export/
  storage/
  audit/
  config.py
prompts/
tests/
docs/
AGENTS.md
README.md
```

Document folders are kinds of documents, not vendor names: supplier invoice, import licence, customs declaration, customs liquidation, carrier invoice, logistics invoice, broker invoice, and unknown. Maersk, ONCF, and Transit Trust are examples, not hardcoded branches.

## Document boundaries

The model reads evidence. Code decides whether a new document starts.

For each page the evidence is:

- document type, or `unknown`
- printed document key, if readable, such as an invoice number, DUM number, or licence number
- printed page marker, if readable, such as “page 2 of 2”
- source page number
- raw text for those items

| Evidence | Boundary |
|---|---|
| Type differs from the previous page | New document |
| Same type, and both keys exist and differ | New document |
| Same type, same key | Same document |
| Same type, page marker continues, and the key does not conflict | Same document |
| Same type, but the key or the continuation is missing or unreadable | New document, status `review` |

Weak evidence splits pages. It does not merge them. Unknown pages stay in the dossier and are excluded from totals.

Two ONCF invoices on back-to-back pages stay two documents because their invoice numbers differ. A two-page Maersk invoice stays one document because the page marker continues and the invoice number does not conflict.

## Field status

The model’s own confidence number is ignored.

| Status | Meaning |
|---|---|
| `missing` | The field is in the schema and no value was read. The value stays null |
| `review` | A value was read, but the page is missing, the schema rejected it, the text is ambiguous, arithmetic failed, or another document conflicts |
| `high` | A value was read, the schema accepted it, the source page is known, and no check conflicts |

A cross-document check may lower `high` to `review`. It never invents a replacement. The printed customs value is compared across the declaration and the liquidation. It is not recalculated.

Every important value keeps:

- normalized value, or null
- raw text
- currency, when it is money
- source document and source page
- status
- method: `ai`, `normalized`, or `user`
- user value, only after a person edits it

An edit does not erase the extracted value. Export uses the user value when one exists and still includes the original in the JSON.

## Validation

Validation is deterministic Python. It does not call the model.

Document checks live next to that document type. Example: invoice lines equal the printed total.

Dossier checks live in one module. Examples: the supplier euro total equals the licence euro total, the bill of lading and containers agree where both are printed, the customs value agrees across customs pages, and the currency is allowed.

Each result has a rule id, severity (`error` or `warning`), status (`passed` or `failed`), the fields involved, and a short message.

A dossier with errors can be exported only after the person sees the errors and chooses to export. That choice is stored.

## Cache

Reuse a saved extraction only when all of these match:

- PDF hash
- model and model version
- prompt version
- schema version
- preprocessing version
- grouping-rules version

If any part changes, extract again. User corrections are stored separately and do not trigger a new model call.

## Untrusted PDF content

Extraction has no tools. The prompt says the document is data and cannot override instructions. Only schema fields are kept.

## Storage

SQLite stores the dossier, its documents, the extraction run, and the review snapshot. The full normalized dossier is JSON on the run. A few identifiers, such as bill of lading and invoice numbers, may be copied into columns so duplicates can be found.

The extraction run records the provider, model, prompt version, schema version, preprocessing version, grouping-rules version, token counts, and estimated cost.

## PoC defaults

- Local single user, no login.
- Originals remain on local disk until a person deletes them.
- Upload cap: 30 MB.
- Currencies: EUR and MAD. USD is accepted as a code only.
- A missing document type raises `review` and still allows an explicit export.
- Company approval is still required before real dossiers are sent to the model vendor.

## Adding a document type later

Add a folder with a schema, a versioned prompt, classifier hints, and any document-level checks. Register it. Do not add a vendor name to a central `if` chain.
