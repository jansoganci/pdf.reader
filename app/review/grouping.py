from app.models import DocumentRecord, Dossier, FieldValue, LineRecord, PageEvidence
from app.validation.rules import validate_dossier


def merge_with_previous(dossier: Dossier, document_id: str) -> Dossier:
    index = _index(dossier, document_id)
    if index == 0:
        raise ValueError("The first document has no previous document.")
    previous = dossier.documents[index - 1]
    current = dossier.documents[index]
    previous.page_numbers = sorted(set(previous.page_numbers + current.page_numbers))
    previous.boundary = _merged_boundary(previous.boundary, current.boundary, set(current.page_numbers))
    _fill_missing_fields(previous, current)
    previous.lines.extend(current.lines)
    current.held_extractions = []
    previous.held_extractions.append(current.model_copy(deep=True))
    previous.review_reason = _join_reason(previous.review_reason, "manual_merge")
    if previous.document_type != current.document_type:
        previous.review_reason = _join_reason(previous.review_reason, "manual_merge_type_conflict")
    dossier.documents.pop(index)
    _revalidate(dossier)
    return dossier


def split_after_page(dossier: Dossier, document_id: str, after_page: int) -> Dossier:
    index = _index(dossier, document_id)
    document = dossier.documents[index]
    if after_page not in document.page_numbers or after_page == max(document.page_numbers):
        raise ValueError("Choose a page that leaves pages on both sides of the split.")
    left_pages = [page for page in document.page_numbers if page <= after_page]
    right_pages = [page for page in document.page_numbers if page > after_page]
    right = DocumentRecord(
        id=_new_id(dossier),
        document_type=document.document_type,
        page_numbers=right_pages,
        review_reason="manual_split",
        fields={name: FieldValue(status="missing") for name in document.fields},
        lines=[],
        boundary=[page for page in document.boundary if page.page_number in right_pages],
    )
    document.page_numbers = left_pages
    document.boundary = [page for page in document.boundary if page.page_number in left_pages]
    document.review_reason = _join_reason(document.review_reason, "manual_split")
    _move_fields(document, right, set(right_pages))
    _restore_held(document, right, set(right_pages))
    if right.boundary:
        right.boundary[0].starts_new_document = True
        right.boundary[0].boundary_reason = "manual_split"
        right.boundary[0].boundary_status = "review"
    dossier.documents.insert(index + 1, right)
    _revalidate(dossier)
    return dossier


def _index(dossier: Dossier, document_id: str) -> int:
    for index, document in enumerate(dossier.documents):
        if document.id == document_id:
            return index
    raise KeyError(document_id)


def _merged_boundary(
    previous: list[PageEvidence],
    current: list[PageEvidence],
    current_pages: set[int],
) -> list[PageEvidence]:
    combined = sorted(previous + current, key=lambda item: item.page_number)
    seen: set[int] = set()
    ordered: list[PageEvidence] = []
    for page in combined:
        if page.page_number in seen:
            continue
        seen.add(page.page_number)
        if page.page_number in current_pages:
            page.starts_new_document = False
            page.boundary_reason = "manual_merge"
            page.boundary_status = "review"
        ordered.append(page)
    return ordered


def _fill_missing_fields(previous: DocumentRecord, current: DocumentRecord) -> None:
    for name, field in current.fields.items():
        kept = previous.fields.get(name)
        if kept is None:
            previous.fields[name] = field.model_copy(deep=True)
            continue
        if _empty(kept) and not _empty(field):
            previous.fields[name] = field.model_copy(deep=True)
            continue
        if not _empty(kept) and not _empty(field) and str(kept.value) != str(field.value):
            if kept.status == "high":
                kept.status = "review"


def _move_fields(left: DocumentRecord, right: DocumentRecord, right_pages: set[int]) -> None:
    for name, field in list(left.fields.items()):
        if field.source_page in right_pages:
            right.fields[name] = field.model_copy(deep=True)
            left.fields[name] = FieldValue(status="missing", source_document_id=left.id)
        elif field.source_page is None and field.value is not None:
            field.status = "review"
    moved: list[LineRecord] = []
    staying: list[LineRecord] = []
    for line in left.lines:
        pages = {item.source_page for item in line.fields.values() if item.source_page is not None}
        if pages and pages <= right_pages:
            moved.append(line)
        else:
            staying.append(line)
    left.lines = staying
    right.lines = moved


def _restore_held(left: DocumentRecord, right: DocumentRecord, right_pages: set[int]) -> None:
    kept = []
    for held in left.held_extractions:
        if set(held.page_numbers) <= right_pages:
            right.fields = {name: field.model_copy(deep=True) for name, field in held.fields.items()}
            right.lines = [line.model_copy(deep=True) for line in held.lines]
            right.document_type = held.document_type
        else:
            kept.append(held)
    left.held_extractions = kept


def _empty(field: FieldValue) -> bool:
    return field.value in (None, "") and field.raw_text in (None, "")


def _join_reason(current: str | None, extra: str) -> str:
    if not current:
        return extra
    if extra in current:
        return current
    return f"{current}; {extra}"


def _new_id(dossier: Dossier) -> str:
    existing = {item.id for item in dossier.documents}
    number = 1
    while f"doc-split-{number}" in existing:
        number += 1
    return f"doc-split-{number}"


def _revalidate(dossier: Dossier) -> None:
    dossier.validation = validate_dossier(dossier)
    dossier.export_with_errors = False
    failed = any(item.status == "failed" and item.severity == "error" for item in dossier.validation)
    dossier.status = "needs_review" if failed else "ready_to_export"
