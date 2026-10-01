import re
from decimal import Decimal

from app.models import DocumentRecord, Dossier, FieldValue, ValidationResult

_TOLERANCE = Decimal("0.01")
_ALLOWED = {"EUR", "MAD", "USD"}


def _money(field: FieldValue | None) -> Decimal | None:
    if field is None or field.value in (None, ""):
        return None
    try:
        return Decimal(str(field.user_value if field.user_value is not None else field.value))
    except Exception:
        return None


def _mark_review(field: FieldValue | None) -> None:
    if field is not None and field.status == "high":
        field.status = "review"


def _result(rule_id: str, ok: bool, message: str, fields: list[str], severity: str = "error") -> ValidationResult:
    return ValidationResult(
        rule_id=rule_id,
        severity=severity,  # type: ignore[arg-type]
        status="passed" if ok else "failed",
        fields=fields,
        message=message,
    )


def validate_dossier(dossier: Dossier) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    for document in dossier.documents:
        results.extend(_document_rules(document))
    results.extend(_cross_rules(dossier))
    return results


def _line_sum(document: DocumentRecord) -> Decimal | None:
    amounts = [_money(line.fields.get("amount")) for line in document.lines]
    present = [amount for amount in amounts if amount is not None]
    if not present:
        return None
    return sum(present, Decimal("0"))


def _before_tax(document: DocumentRecord) -> Decimal | None:
    total = _money(document.fields.get("total_amount"))
    tax = _money(document.fields.get("tax_amount"))
    net = _money(document.fields.get("net_amount"))
    if total is not None and tax is not None:
        return total - tax
    if net is not None:
        return net
    return total


def _document_rules(document: DocumentRecord) -> list[ValidationResult]:
    results = []
    total = _money(document.fields.get("total_amount"))
    net = _money(document.fields.get("net_amount"))
    tax = _money(document.fields.get("tax_amount"))
    lines = _line_sum(document)
    if document.document_type not in {"customs_declaration", "customs_liquidation"}:
        target = _before_tax(document)
        if lines is not None and target is not None:
            ok = abs(lines - target) <= _TOLERANCE
            if not ok:
                _mark_review(document.fields.get("total_amount"))
            results.append(_result("lines_sum_to_total", ok, "Invoice lines equal the amount before tax.", [document.id]))
    fob = _money(document.fields.get("fob_amount"))
    freight = _money(document.fields.get("freight_amount"))
    if fob is not None and freight is not None and total is not None:
        ok = abs((fob + freight) - total) <= _TOLERANCE
        if not ok:
            _mark_review(document.fields.get("total_amount"))
        results.append(_result("fob_plus_freight", ok, "FOB plus freight equals the printed total.", [document.id]))
    if net is not None and tax is not None and total is not None:
        lines_explain_total = lines is not None and abs((lines + tax) - total) <= _TOLERANCE
        ok = abs((net + tax) - total) <= _TOLERANCE or lines_explain_total
        if not ok:
            _mark_review(document.fields.get("total_amount"))
        results.append(_result("net_plus_tax", ok, "Net plus tax equals the printed total.", [document.id]))
    currency = document.fields.get("currency")
    if currency and currency.value and currency.value not in _ALLOWED:
        _mark_review(currency)
        results.append(
            _result("supported_currency", False, "Currency is not EUR, MAD, or USD.", [document.id], "warning")
        )
    return results


def _bl_keys(value: str) -> set[str]:
    found = set(re.findall(r"\d{8,}", value))
    if found:
        return found
    compact = re.sub(r"\s+", "", value)
    return {compact} if compact else set()


def _first(dossier: Dossier, document_type: str) -> DocumentRecord | None:
    return next((item for item in dossier.documents if item.document_type == document_type), None)


def _cross_rules(dossier: Dossier) -> list[ValidationResult]:
    results = []
    supplier = _first(dossier, "supplier_invoice")
    licence = _first(dossier, "import_licence")
    if supplier and licence:
        left = _money(supplier.fields.get("total_amount"))
        right = _money(licence.fields.get("total_amount"))
        if left is not None and right is not None:
            ok = abs(left - right) <= _TOLERANCE
            if not ok:
                _mark_review(supplier.fields.get("total_amount"))
                _mark_review(licence.fields.get("total_amount"))
            results.append(_result("supplier_equals_licence", ok, "Supplier total equals the licence total.", []))
    declaration = _first(dossier, "customs_declaration")
    liquidation = _first(dossier, "customs_liquidation")
    if declaration and liquidation:
        left = _money(declaration.fields.get("customs_value"))
        right = _money(liquidation.fields.get("customs_value"))
        if left is not None and right is not None:
            ok = abs(left - right) <= _TOLERANCE
            if not ok:
                _mark_review(declaration.fields.get("customs_value"))
                _mark_review(liquidation.fields.get("customs_value"))
            results.append(
                _result("customs_value_matches", ok, "Printed customs values match across customs pages.", [])
            )
    bls = []
    containers = []
    numbers: list[str] = []
    for document in dossier.documents:
        bl = document.fields.get("bill_of_lading")
        if bl and bl.value:
            bls.append(_bl_keys(str(bl.value)))
        box = document.fields.get("containers")
        if box and box.value:
            found = re.findall(r"[A-Z]{4}\d{7}", str(box.value).upper())
            if found:
                containers.append(tuple(sorted(set(found))))
        number = document.fields.get("document_number")
        if number and number.value:
            numbers.append(str(number.value))
    if len(bls) > 1:
        ok = bool(set.intersection(*bls))
        results.append(_result("bill_of_lading_matches", ok, "Bill of lading values match." if ok else "Bill of lading values differ.", []))
    if len(set(containers)) > 1:
        results.append(_result("containers_match", False, "Container lists differ.", []))
    elif len(containers) > 1:
        results.append(_result("containers_match", True, "Container lists match.", []))
    if len(numbers) != len(set(numbers)):
        results.append(_result("duplicate_invoice_number", False, "The same document number appears twice.", []))
    present = {item.document_type for item in dossier.documents}
    for expected in (
        "supplier_invoice",
        "import_licence",
        "customs_declaration",
        "customs_liquidation",
        "carrier_invoice",
        "logistics_invoice",
        "broker_invoice",
    ):
        if expected not in present:
            results.append(
                _result("missing_document_type", False, f"{expected} was not found.", [], "warning")
            )
    return results
