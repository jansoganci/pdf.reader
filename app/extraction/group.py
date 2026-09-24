from app.extraction.normalize import normalize_key, parse_marker
from app.models import DocumentType, PageEvidence


def _keys_conflict(left: str | None, right: str | None) -> bool:
    return bool(left and right and left != right)


def starts_new(previous: PageEvidence | None, page: PageEvidence) -> tuple[bool, str, str]:
    if previous is None:
        return True, "first_page", "high"
    if page.document_type != previous.document_type:
        return True, "type_changed", "high"
    if page.document_key and previous.document_key and page.document_key != previous.document_key:
        return True, "key_changed", "high"
    if page.document_key and previous.document_key and page.document_key == previous.document_key:
        return False, "same_key", "high"
    continues = (
        previous.marker_current is not None
        and page.marker_current is not None
        and previous.marker_count is not None
        and page.marker_count == previous.marker_count
        and page.marker_current == previous.marker_current + 1
    )
    if continues and not _keys_conflict(previous.document_key, page.document_key):
        return False, "page_continues", "high"
    return True, "insufficient_evidence", "review"


def build_evidence(
    page_number: int,
    document_type: DocumentType,
    document_key: str | None,
    page_marker: str | None,
) -> PageEvidence:
    current, count = parse_marker(page_marker)
    return PageEvidence(
        page_number=page_number,
        document_type=document_type,
        document_key_raw=document_key,
        document_key=normalize_key(document_key),
        page_marker_raw=page_marker,
        marker_current=current,
        marker_count=count,
    )


def group_pages(pages: list[PageEvidence]) -> list[list[PageEvidence]]:
    ordered = sorted(pages, key=lambda item: item.page_number)
    groups: list[list[PageEvidence]] = []
    previous: PageEvidence | None = None
    for page in ordered:
        new, reason, status = starts_new(previous, page)
        page.starts_new_document = new
        page.boundary_reason = reason
        page.boundary_status = status  # type: ignore[assignment]
        if new or not groups:
            groups.append([page])
        else:
            groups[-1].append(page)
        previous = page
    return groups
