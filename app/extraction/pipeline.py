import uuid
from pathlib import Path

from pydantic import ValidationError

from app.documents.registry import BoundaryPayload, ClassifyPayload, MoneyDocument
from app.extraction.cost import estimate_cost
from app.extraction.group import build_evidence, group_pages
from app.extraction.normalize import field_from_raw, lines_from_raw
from app.extraction.structured import call_structured
from app.models import DocumentRecord, Dossier, FieldValue, Usage
from app.pdf.render import cleanup_renders, render_pdf
from app.providers.base import AIProvider, ProviderRefusal, ProviderSuccess, ProviderTransportError
from app.validation.rules import validate_dossier

_MONEY_FIELDS = (
    "supplier_name",
    "document_number",
    "document_date",
    "currency",
    "net_amount",
    "tax_amount",
    "total_amount",
    "fob_amount",
    "freight_amount",
    "customs_value",
    "exchange_rate",
    "insurance_amount",
    "bill_of_lading",
    "containers",
    "hs_code",
    "package_count",
    "regime",
)


def process_pdf(
    data: bytes,
    filename: str,
    sha256: str,
    signature: str,
    provider: AIProvider,
    render_dir: Path,
) -> Dossier:
    pages = render_pdf(data, render_dir)
    images = [image for _, image in pages]
    usage = Usage()
    try:
        classify_call, classified = call_structured(provider.classify_pages, ClassifyPayload, images)
        _add_usage(usage, classify_call)
        if classified is None or not isinstance(classified, ClassifyPayload):
            return _failed(filename, sha256, signature, usage, "classification_failed")
        by_page = {item.page_number: item for item in classified.pages}
        if set(by_page) != set(range(1, len(pages) + 1)):
            return _failed(filename, sha256, signature, usage, "classification_pages_incomplete")
        boundary_call, boundary = call_structured(provider.read_boundary_evidence, BoundaryPayload, images)
        _add_usage(usage, boundary_call)
        if not isinstance(boundary, BoundaryPayload):
            return _failed(filename, sha256, signature, usage, "boundary_failed")
        keys = {item.page_number: item for item in boundary.pages}
        evidence = []
        for number in range(1, len(pages) + 1):
            label = by_page[number]
            found = keys.get(number)
            evidence.append(
                build_evidence(
                    number,
                    label.document_type,
                    None if found is None else found.document_key,
                    None if found is None else found.page_marker,
                )
            )
        documents: list[DocumentRecord] = []
        for index, group in enumerate(group_pages(evidence), start=1):
            document_type = group[0].document_type
            group_images = [images[page.page_number - 1] for page in group]
            call, extracted = call_structured(
                lambda imgs, note, kind=document_type: provider.extract_document(kind, imgs, note),
                MoneyDocument,
                group_images,
            )
            _add_usage(usage, call)
            document_id = f"doc-{index}"
            reason = None
            extracted_model = extracted if isinstance(extracted, MoneyDocument) else MoneyDocument()
            if isinstance(call, ProviderTransportError):
                reason = "transport"
            elif isinstance(call, ProviderRefusal):
                reason = "refusal"
            elif isinstance(extracted, ValidationError) or not isinstance(extracted, MoneyDocument):
                reason = "schema_mismatch"
            fields = {
                name: field_from_raw(getattr(extracted_model, name), kind=_kind(name), document_id=document_id)
                for name in _MONEY_FIELDS
            }
            if reason:
                for field in fields.values():
                    if field.status == "high":
                        field.status = "review"
            documents.append(
                DocumentRecord(
                    id=document_id,
                    document_type=document_type,
                    page_numbers=[page.page_number for page in group],
                    review_reason=reason,
                    fields=fields,
                    lines=lines_from_raw(extracted_model.lines, document_id),
                    boundary=group,
                )
            )
        dossier = Dossier(
            id=str(uuid.uuid4()),
            filename=filename,
            sha256=sha256,
            pipeline_signature=signature,
            status="needs_review",
            documents=documents,
            usage=usage,
            estimated_cost_usd=estimate_cost(usage),
        )
        dossier.validation = validate_dossier(dossier)
        if any(item.status == "failed" and item.severity == "error" for item in dossier.validation):
            dossier.status = "needs_review"
        else:
            dossier.status = "ready_to_export"
        return dossier
    finally:
        cleanup_renders(render_dir)


def _kind(name: str) -> str:
    if name.endswith("_date"):
        return "date"
    if name == "currency":
        return "currency"
    if name.endswith("_amount") or name in {"customs_value", "exchange_rate"}:
        return "money"
    return "text"


def _add_usage(total: Usage, call) -> None:
    if call is None or not hasattr(call, "usage"):
        return
    usage = call.usage
    total.input_tokens += usage.input_tokens
    total.output_tokens += usage.output_tokens
    total.cache_creation_input_tokens += usage.cache_creation_input_tokens
    total.cache_read_input_tokens += usage.cache_read_input_tokens
    total.duration_ms += usage.duration_ms


def _failed(filename: str, sha256: str, signature: str, usage: Usage, reason: str) -> Dossier:
    return Dossier(
        id=str(uuid.uuid4()),
        filename=filename,
        sha256=sha256,
        pipeline_signature=signature,
        status="failed",
        documents=[
            DocumentRecord(
                id="doc-1",
                document_type="unknown",
                page_numbers=[],
                review_reason=reason,
                fields={"document_number": FieldValue(status="missing")},
            )
        ],
        usage=usage,
    )
