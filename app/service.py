import hashlib
import logging
from pathlib import Path

from app.config import settings
from app.extraction.pipeline import process_pdf
from app.extraction.signature import pipeline_signature
from app.export.writers import dossier_json, fields_csv, lines_csv
from app.models import Dossier
from app.pdf.render import PdfRejected
from app.providers.fake import FakeProvider
from app.storage import db
from app.validation.rules import validate_dossier

log = logging.getLogger("dossier")


def configure_logging() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(settings.data_dir / "app.log"),
        ],
    )


def provider_for():
    if settings.extraction_provider == "fake":
        return FakeProvider()
    if settings.extraction_provider == "anthropic":
        from app.providers.anthropic import AnthropicProvider

        return AnthropicProvider()
    raise RuntimeError("Unknown extraction provider.")


def process_upload(data: bytes, filename: str, provider=None) -> Dossier:
    configure_logging()
    digest = hashlib.sha256(data).hexdigest()
    signature = pipeline_signature()
    cached = db.find_cached(digest, signature)
    if cached is not None:
        log.info("cache hit dossier=%s", cached.id)
        return cached
    chosen = provider if provider is not None else provider_for()
    render_dir = settings.data_dir / "renders" / digest
    try:
        dossier = process_pdf(data, filename, digest, signature, chosen, render_dir)
    except PdfRejected:
        raise
    path = db.original_path(dossier.id)
    path.write_bytes(data)
    db.save_dossier(dossier)
    log.info(
        "processed dossier=%s status=%s duration_ms=%s tokens_in=%s tokens_out=%s",
        dossier.id,
        dossier.status,
        dossier.usage.duration_ms,
        dossier.usage.input_tokens,
        dossier.usage.output_tokens,
    )
    return dossier


def list_dossiers() -> list[dict]:
    return db.list_dossiers()


def get_dossier(dossier_id: str) -> Dossier | None:
    return db.get_dossier(dossier_id)


def correct_field(dossier_id: str, document_id: str, field_name: str, user_value: str, note: str = "") -> Dossier:
    dossier = db.get_dossier(dossier_id)
    if dossier is None:
        raise KeyError(dossier_id)
    document = next(item for item in dossier.documents if item.id == document_id)
    field = document.fields[field_name]
    field.user_value = user_value
    field.user_raw_note = note or None
    field.method = "user"
    dossier.validation = validate_dossier(dossier)
    dossier.export_with_errors = False
    db.update_current(dossier, False)
    log.info("correction dossier=%s document=%s field=%s", dossier_id, document_id, field_name)
    return dossier


def mark_export_with_errors(dossier_id: str, allowed: bool) -> Dossier:
    dossier = db.get_dossier(dossier_id)
    if dossier is None:
        raise KeyError(dossier_id)
    dossier.export_with_errors = allowed
    db.update_current(dossier, allowed)
    return dossier


def export_dossier(dossier_id: str, kind: str) -> Path:
    dossier = db.get_dossier(dossier_id)
    if dossier is None:
        raise KeyError(dossier_id)
    errors = [item for item in dossier.validation if item.status == "failed" and item.severity == "error"]
    if errors and not dossier.export_with_errors:
        raise PermissionError("Export is blocked until errors are acknowledged.")
    folder = settings.data_dir / "exports" / dossier_id
    folder.mkdir(parents=True, exist_ok=True)
    if kind == "json":
        content = dossier_json(dossier).encode()
        path = folder / "dossier.json"
    elif kind == "fields_csv":
        content = fields_csv(dossier).encode()
        path = folder / "fields.csv"
    elif kind == "lines_csv":
        content = lines_csv(dossier).encode()
        path = folder / "lines.csv"
    else:
        raise ValueError(kind)
    path.write_bytes(content)
    db.record_export(dossier_id, kind, path, content)
    return path
