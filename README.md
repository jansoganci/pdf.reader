# Import dossier reader

Finance uses this tool to read one import-dossier PDF, check the reading, correct it, and export JSON and CSV.

Phase 1 does not post to SAP. It does not choose GL accounts, tax codes, reason codes, or clearing account 159220010.

## How it will run

The PoC is a local, single-user app:

Streamlit handles the screen only. A Python service owns preprocessing, classification, document boundaries, extraction, normalization, validation, storage, and export.

Original PDFs stay in a local data folder outside git. SQLite stores the dossier, the extraction run, and the review. An API key belongs in a local `.env` file, which is never committed.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
streamlit run app/ui/app.py --server.port 8765 --server.address 127.0.0.1
```

The default provider is `fake`. It does not call Anthropic and it does not invent amounts. A live call also requires `LIVE_EXTRACTION=1` and `ANTHROPIC_API_KEY`. Do not set that until live testing is explicitly approved.

## Phase 1 limits

- One PDF upload, maximum 30 MB.
- Currencies recognized in this flow: EUR and MAD. USD may appear as a code and is not specially processed.
- A missing document type is flagged for review. The person can still export.
- Pages are not merged into one document unless boundary evidence is positive.
- The same file is not sent to the model again when the full cache key matches.
- Real dossiers may be sent to the model vendor only after the company confirms that this is allowed.

## Decisions

The architecture, security rules, and assistant rules live in:

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/SECURITY.md](docs/SECURITY.md)
- [AGENTS.md](AGENTS.md)
