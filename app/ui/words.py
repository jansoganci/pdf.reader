"""The paper's terms and sentences, looked up in the current language (`app/ui/lang`)."""

import re
from decimal import Decimal, InvalidOperation

from app.models import DocumentRecord, FieldValue
from app.ui.lang import has, t

COPY_FIELDS = {
    "supplier_invoice": [
        "supplier_name", "document_number", "document_date", "currency",
        "total_amount", "fob_amount", "freight_amount",
    ],
    "import_licence": [
        "supplier_name", "document_number", "document_date", "currency",
        "total_amount", "fob_amount", "freight_amount", "hs_code", "regime",
    ],
    "customs_declaration": [
        "document_number", "document_date", "customs_value", "exchange_rate",
        "bill_of_lading", "containers", "hs_code", "package_count",
    ],
    "customs_liquidation": [
        "document_number", "document_date", "customs_value", "tax_amount", "total_amount",
    ],
    "carrier_invoice": [
        "supplier_name", "document_number", "document_date", "currency",
        "net_amount", "tax_amount", "total_amount", "bill_of_lading", "containers",
    ],
    "logistics_invoice": [
        "supplier_name", "document_number", "document_date", "currency",
        "net_amount", "tax_amount", "total_amount", "bill_of_lading", "containers",
    ],
    "broker_invoice": [
        "supplier_name", "document_number", "document_date", "currency",
        "net_amount", "tax_amount", "total_amount",
    ],
    "unknown": ["supplier_name", "document_number", "document_date", "total_amount"],
}

# Keys of the values a person types. The labels are `manual.<key>` in the catalog.
FILE_MANUAL = ("order_number", "sap_exchange_rate")

PAPER_MANUAL = ("vendor_code", "posting_date", "tax_code", "reason_code", "gl_account")

# Broker invoices (Transit Trust and others) carry a different tax code and
# reason code per service line, not one for the whole paper. Maersk, ONCF,
# and every other paper type keep the single pair in PAPER_MANUAL above.
LINE_MANUAL = ("tax_code", "reason_code")


def manual_label(key: str) -> str:
    return t(f"manual.{key}")


def not_on_the_page() -> str:
    """Shown in place of printed text when a field was not read."""
    return t("form.not_on_page")


def shown_keys(document: DocumentRecord) -> list[str]:
    keys = list(COPY_FIELDS.get(document.document_type, []))
    for key, field in document.fields.items():
        if key in keys:
            continue
        if shown_value(field) not in (None, "") or field.raw_text or field.status == "review":
            keys.append(key)
    return [key for key in keys if key in document.fields]


def paper_name(document_type: str) -> str:
    key = f"paper.{document_type}"
    return t(key if has(key) else "paper.unknown")


def field_name(document_type: str, key: str) -> str:
    if key == "document_number":
        number = f"number.{document_type}"
        return t(number if has(number) else "number.unknown")
    name = f"field.{key}"
    return t(name) if has(name) else key.replace("_", " ").capitalize()


def shown_value(field: FieldValue):
    return field.user_value if field.user_value is not None else field.value


def money_text(value, currency: str | None) -> str:
    if value in (None, ""):
        return ""
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return str(value)
    text = f"{number:,.2f}"
    if currency:
        return f"{text} {currency}"
    return text


def pages_text(pages: list[int]) -> str:
    if not pages:
        return t("pages.none")
    if len(pages) == 1:
        return t("pages.one", first=pages[0])
    if pages == list(range(pages[0], pages[-1] + 1)):
        return t("pages.range", first=pages[0], last=pages[-1])
    return t("pages.list", list=", ".join(str(page) for page in pages))


def check_sentence(rule_id: str, message: str, paper: str | None, passed: bool = False) -> str:
    """One check as a sentence. Matched by rule id; a rule the catalog does not know shows the
    message validation gave it."""
    if rule_id == "missing_document_type":
        code = message.split(" ", 1)[0]
        return t("check.missing_document", paper=paper_name(code))
    key = f"check.{'passed' if passed else 'failed'}.{rule_id}"
    sentence = t(key) if has(key) else message
    if paper:
        return t("check.with_paper", paper=paper, sentence=sentence)
    return sentence


_REJECTIONS = {
    "File was not accepted. The limit is 30 MB.": "reject.too_big",
    "File was not accepted. Upload one PDF.": "reject.not_pdf",
    "File could not be opened.": "reject.unreadable",
    "File was not accepted. Encrypted PDFs are not supported.": "reject.encrypted",
    "File could not be opened. A page image is too large.": "reject.page_too_large",
}
_PAGE_LIMIT = re.compile(r"^File was not accepted\. The limit is (\d+) pages\.$")


def rejection_text(message: str) -> str:
    """The reason a PDF was refused, in the current language. `render_pdf` words its refusals in
    English; a refusal this does not know is shown as it came."""
    key = _REJECTIONS.get(message)
    if key:
        return t(key)
    match = _PAGE_LIMIT.match(message)
    if match:
        return t("reject.too_many_pages", limit=match.group(1))
    return message


def issued_by(document: DocumentRecord) -> str | None:
    field = document.fields.get("supplier_name")
    if field is None:
        return None
    value = shown_value(field)
    return None if value in (None, "") else str(value)
