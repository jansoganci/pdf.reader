"""What the review screen shows, as plain data.

No Streamlit and no service calls in here (docs/UI_PLAN.md section 3). A `Dossier`
goes in; plain, frozen view objects come out. All the "which words, which tier,
which page" decisions live here so they can be tested without a browser.

Severity -> tier is decided once, in `check_tier`: an `error` is `crit`, a
`warning` is `warn`. Nothing here decides accounting; it only chooses how to show
what validation already found.
"""

from dataclasses import dataclass

from app.models import DocumentRecord, Dossier, ValidationResult
from app.ui.components import TIER_WORDS
from app.ui.words import (
    PAPER_MANUAL,
    check_sentence as failed_check_sentence,
    field_name,
    issued_by,
    money_text,
    pages_text,
    paper_name,
    shown_keys,
    shown_value,
)

MONEY_KEYS = {
    "net_amount", "tax_amount", "total_amount", "fob_amount",
    "freight_amount", "customs_value", "insurance_amount",
}

# Headline figures above the paper tabs: (document type, label, field).
TOTALS = (
    ("supplier_invoice", "Supplier invoice", "total_amount"),
    ("customs_declaration", "Customs value", "customs_value"),
    ("customs_liquidation", "Customs payment", "total_amount"),
    ("carrier_invoice", "Shipping invoice", "total_amount"),
)

LINE_CODE_TYPES = ("broker_invoice",)  # one tax code and one reason code per service line
CUSTOMS_TYPES = ("customs_declaration", "customs_liquidation")


@dataclass(frozen=True)
class TotalsCell:
    label: str
    amount: str
    sub: str
    needs_check: bool


@dataclass(frozen=True)
class RowView:
    key: str
    label: str
    value_text: str
    printed_text: str | None
    needs_check: bool
    missing: bool = False  # nothing was read and nobody typed anything: say so, never invent a value
    edited: bool = False  # a person changed this value; the original is kept in the data


@dataclass(frozen=True)
class LineView:
    index: int
    text: str


@dataclass(frozen=True)
class CheckView:
    tier: str
    text: str


@dataclass(frozen=True)
class PaperView:
    id: str
    document_type: str
    position: int
    tab_label: str
    title: str
    subline: str
    page_numbers: tuple[int, ...]
    default_page: int | None
    rows: tuple[RowView, ...]
    lines: tuple[LineView, ...]
    line_codes: bool
    typed_fields: tuple[tuple[str, str], ...]
    typed_notes: tuple[str, ...]
    failed_checks: tuple[CheckView, ...]
    passed_checks: tuple[str, ...]


@dataclass(frozen=True)
class DossierView:
    id: str
    filename: str
    paper_count: int
    tier: str
    blocking_count: int
    banner_text: str
    totals: tuple[TotalsCell, ...]
    papers: tuple[PaperView, ...]


# Keys that tie typed values to a paper. They are data keys (they go to the service
# as `manual`), and the widget keys are built from them in state.py.
def paper_store_key(document_id: str, key: str) -> str:
    return f"{document_id}:{key}"


def line_store_key(document_id: str, index: int, key: str) -> str:
    return f"{document_id}:line:{index}:{key}"


def _currency(document: DocumentRecord, key: str) -> str | None:
    if key == "customs_value":
        return "MAD"
    if document.document_type == "customs_liquidation" and key in MONEY_KEYS:
        field = document.fields.get("currency")
        value = None if field is None else shown_value(field)
        return str(value) if value not in (None, "") else "MAD"
    field = document.fields.get("currency")
    if field is None:
        return None
    value = shown_value(field)
    return None if value in (None, "") else str(value)


def display(document: DocumentRecord, key: str) -> str:
    """The value of one field as the person reads it. Empty stays empty."""
    field = document.fields.get(key)
    if field is None:
        return ""
    value = shown_value(field)
    if value in (None, ""):
        return ""
    if key in MONEY_KEYS:
        return money_text(value, _currency(document, key))
    return str(value)


def headline_amount(document: DocumentRecord) -> str:
    for key in ("total_amount", "customs_value"):
        text = display(document, key)
        if text:
            return text
    return ""


def check_tier(item: ValidationResult) -> str:
    return "crit" if item.severity == "error" else "warn"


def check_sentence(dossier: Dossier, item: ValidationResult) -> str:
    names = []
    for document_id in item.fields:
        found = next((doc for doc in dossier.documents if doc.id == document_id), None)
        if found is not None:
            names.append(paper_name(found.document_type))
    paper = names[0] if len(names) == 1 else None
    if item.status == "passed":
        return f"{paper}: {item.message}" if paper else item.message
    return failed_check_sentence(item.rule_id, item.message, paper)


def tab_label(document: DocumentRecord) -> str:
    name = paper_name(document.document_type)
    needs_check = any(field.status == "review" for field in document.fields.values())
    return f"• {name}" if needs_check else name


def default_page(document: DocumentRecord) -> int | None:
    """Open on the page a flagged field was actually read from. Fall back to the
    paper's first page when nothing needs a check."""
    if not document.page_numbers:
        return None
    for key in shown_keys(document):
        field = document.fields[key]
        if field.status == "review" and field.source_page in document.page_numbers:
            return field.source_page
    return document.page_numbers[0]


def paper_manual_fields(document_type: str) -> list[tuple[str, str]]:
    """The values a person types for one paper, which no paper prints."""
    fields = list(PAPER_MANUAL)
    if document_type in LINE_CODE_TYPES:
        # Each service line gets its own tax code and reason code instead.
        fields = [(key, label) for key, label in fields if key not in ("tax_code", "reason_code")]
    if document_type in CUSTOMS_TYPES:
        fields = fields + [("sap_reference", "SAP reference")]
    return fields


def review_count(dossier: Dossier) -> int:
    """How many values were read but still need a person to look (field status `review`)."""
    return sum(1 for document in dossier.documents for field in document.fields.values() if field.status == "review")


def dossier_tier(dossier: Dossier) -> str:
    """crit: a check failed with severity error. warn: any other failed check, or any value in
    `review`. good: nothing to look at. (docs/design.md section 4)"""
    failed = [item for item in dossier.validation if item.status == "failed"]
    if any(item.severity == "error" for item in failed):
        return "crit"
    return "warn" if failed or review_count(dossier) else "good"


def banner_text(tier: str, failed_count: int, blocking_count: int, review_values: int = 0) -> str:
    if tier == "crit":
        return f"{blocking_count} item(s) block the download until you check them."
    if tier == "warn":
        if failed_count:
            return f"{failed_count} item(s) might need a second look before you download."
        return f"{review_values} value(s) might need a second look before you download."
    return TIER_WORDS["good"] + "."


def totals(dossier: Dossier) -> tuple[TotalsCell, ...]:
    cells = []
    for kind, label, key in TOTALS:
        found = next((item for item in dossier.documents if item.document_type == kind), None)
        if found is None:
            continue
        field = found.fields.get(key)
        who = issued_by(found)
        if kind == "customs_declaration":
            sub = "Copied from the customs papers"
        elif who:
            sub = f"Issued by {who}"
        else:
            sub = ""
        cells.append(
            TotalsCell(label, display(found, key) or "Not read", sub, field is not None and field.status == "review")
        )
    return tuple(cells)


def _rows(document: DocumentRecord) -> tuple[RowView, ...]:
    rows = []
    for key in shown_keys(document):
        field = document.fields[key]
        value_text = display(document, key)
        edited = field.user_value is not None
        rows.append(
            RowView(
                key=key,
                label=field_name(document.document_type, key),
                value_text=value_text,
                printed_text=field.raw_text,
                needs_check=field.status == "review",
                missing=field.status == "missing" and not value_text and not edited,
                edited=edited,
            )
        )
    return tuple(rows)


def _lines(document: DocumentRecord) -> tuple[LineView, ...]:
    out = []
    for index, line in enumerate(document.lines, start=1):
        description = line.fields.get("description")
        amount = line.fields.get("amount")
        description_text = "" if description is None else str(shown_value(description) or "")
        amount_text = "" if amount is None else str(shown_value(amount) or "")
        out.append(LineView(index, f"{index}. {description_text} {amount_text}".strip()))
    return tuple(out)


def _typed_notes(document_type: str) -> tuple[str, ...]:
    notes = []
    if document_type == "customs_liquidation":
        notes.append("Payment number above is the liquidation number. SAP reference stays empty until you type it.")
    if document_type in LINE_CODE_TYPES:
        notes.append("Each service line above has its own Tax code and Reason code.")
    return tuple(notes)


def _paper(dossier: Dossier, document: DocumentRecord, position: int) -> PaperView:
    who = issued_by(document)
    subline = " · ".join(
        bit
        for bit in (
            pages_text(document.page_numbers),
            f"Issued by {who}" if who else "",
            headline_amount(document),
        )
        if bit
    )
    relevant = lambda item: not item.fields or document.id in item.fields  # noqa: E731
    failed = [item for item in dossier.validation if item.status == "failed" and relevant(item)]
    passed = [item for item in dossier.validation if item.status == "passed" and relevant(item)]
    return PaperView(
        id=document.id,
        document_type=document.document_type,
        position=position,
        tab_label=tab_label(document),
        title=paper_name(document.document_type),
        subline=subline,
        page_numbers=tuple(document.page_numbers),
        default_page=default_page(document),
        rows=_rows(document),
        lines=_lines(document),
        line_codes=document.document_type in LINE_CODE_TYPES,
        typed_fields=tuple(paper_manual_fields(document.document_type)),
        typed_notes=_typed_notes(document.document_type),
        failed_checks=tuple(CheckView(check_tier(item), check_sentence(dossier, item)) for item in failed),
        passed_checks=tuple(check_sentence(dossier, item) for item in passed),
    )


def build(dossier: Dossier) -> DossierView:
    failed = [item for item in dossier.validation if item.status == "failed"]
    blocking = [item for item in failed if item.severity == "error"]
    tier = dossier_tier(dossier)
    return DossierView(
        id=dossier.id,
        filename=dossier.filename,
        paper_count=len(dossier.documents),
        tier=tier,
        blocking_count=len(blocking),
        banner_text=banner_text(tier, len(failed), len(blocking), review_count(dossier)),
        totals=totals(dossier),
        papers=tuple(_paper(dossier, document, index) for index, document in enumerate(dossier.documents)),
    )
