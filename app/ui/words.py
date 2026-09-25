from decimal import Decimal, InvalidOperation

from app.models import DocumentRecord, FieldValue

PAPER_NAMES = {
    "supplier_invoice": "Supplier invoice",
    "import_licence": "Import licence",
    "customs_declaration": "Customs declaration",
    "customs_liquidation": "Customs payment",
    "carrier_invoice": "Shipping invoice",
    "logistics_invoice": "Logistics invoice",
    "broker_invoice": "Broker invoice",
    "unknown": "Other page",
}

FIELD_NAMES = {
    "supplier_name": "Issued by",
    "document_number": "Number",
    "document_date": "Date",
    "currency": "Currency",
    "net_amount": "Net",
    "tax_amount": "Tax",
    "total_amount": "Total",
    "fob_amount": "FOB",
    "freight_amount": "Freight",
    "customs_value": "Customs value",
    "exchange_rate": "Exchange rate",
    "insurance_amount": "Insurance",
    "bill_of_lading": "Bill of lading",
    "containers": "Containers",
    "hs_code": "HS code",
    "package_count": "Packages",
    "regime": "Regime",
}

NUMBER_NAMES = {
    "supplier_invoice": "Invoice number",
    "import_licence": "Licence number",
    "customs_declaration": "Declaration number",
    "customs_liquidation": "Payment number",
    "carrier_invoice": "Invoice number",
    "logistics_invoice": "Invoice number",
    "broker_invoice": "Invoice number",
    "unknown": "Number",
}

FILE_STATUS = {
    "needs_review": "Needs a check",
    "ready_to_export": "Ready to download",
    "failed": "Could not be read",
}


def paper_name(document_type: str) -> str:
    return PAPER_NAMES.get(document_type, "Other page")


def field_name(document_type: str, key: str) -> str:
    if key == "document_number":
        return NUMBER_NAMES.get(document_type, "Number")
    return FIELD_NAMES.get(key, key.replace("_", " ").capitalize())


def file_status(status: str) -> str:
    return FILE_STATUS.get(status, "Needs a check")


def shown_value(field: FieldValue):
    return field.user_value if field.user_value is not None else field.value


def money_text(value, currency: str | None) -> str:
    if value in (None, ""):
        return ""
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return str(value)
    places = abs(number.as_tuple().exponent)
    text = f"{number:,.{places}f}" if places > 2 else f"{number:,.2f}"
    if currency:
        return f"{text} {currency}"
    return text


def pages_text(pages: list[int]) -> str:
    if not pages:
        return "No pages"
    if len(pages) == 1:
        return f"Page {pages[0]}"
    if pages == list(range(pages[0], pages[-1] + 1)):
        return f"Pages {pages[0]}–{pages[-1]}"
    return "Pages " + ", ".join(str(page) for page in pages)


FAILED_CHECKS = {
    "lines_sum_to_total": "The lines on the page do not add up to the total.",
    "net_plus_tax": "Net plus tax does not equal the total.",
    "fob_plus_freight": "FOB plus freight does not equal the total.",
    "supplier_equals_licence": "The supplier total does not match the import licence.",
    "customs_value_matches": "The customs value is not the same on both customs papers.",
    "bill_of_lading_matches": "The bill of lading is not the same on every paper.",
    "containers_match": "The containers are not the same on every paper.",
    "duplicate_invoice_number": "The same number appears on two papers.",
    "supported_currency": "This currency needs a check.",
}


def check_sentence(rule_id: str, message: str, paper: str | None) -> str:
    if rule_id == "missing_document_type":
        code = message.split(" ", 1)[0]
        return f"{paper_name(code)} was not in this file."
    sentence = FAILED_CHECKS.get(rule_id, message)
    if paper:
        return f"{paper}: {sentence}"
    return sentence


def issued_by(document: DocumentRecord) -> str | None:
    field = document.fields.get("supplier_name")
    if field is None:
        return None
    value = shown_value(field)
    return None if value in (None, "") else str(value)
