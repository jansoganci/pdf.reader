import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from app.documents.common import RawField, RawLine
from app.models import FieldValue, LineRecord

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8,     "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "janvier": 1, "fevrier": 2, "février": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "aout": 8, "août": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12, "décembre": 12,
}


def parse_decimal(raw: str | None) -> tuple[Decimal | None, bool]:
    """Return (value, ambiguous). Ambiguous values stay null."""
    if raw is None or not str(raw).strip():
        return None, False
    text = str(raw).strip().replace(" ", "").replace("\u00a0", "")
    text = re.sub(r"[^0-9,.\-]", "", text)
    if not text or text in {"-", ".", ","}:
        return None, True
    has_comma = "," in text
    has_dot = "." in text
    if has_comma and has_dot:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif has_comma or has_dot:
        sep = "," if has_comma else "."
        left, right = text.rsplit(sep, 1)
        if sep in left:
            digits = left.replace(sep, "")
            if len(right) != 3 or not digits.replace("-", "").isdigit() or not right.isdigit():
                return None, True
            text = digits + right
        else:
            if right == "" or not left.replace("-", "").isdigit() or not right.isdigit():
                return None, True
            if len(right) == 3 and len(left.replace("-", "")) <= 3:
                return None, True
            text = left + "." + right
    try:
        return Decimal(text), False
    except InvalidOperation:
        return None, True


def parse_date(raw: str | None) -> tuple[str | None, bool]:
    if raw is None or not str(raw).strip():
        return None, False
    text = str(raw).strip()
    for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date().isoformat(), False
        except ValueError:
            continue
    french = re.search(r"(\d{1,2})\s+([A-Za-zÀ-ÿ]+)\s+(\d{4})", text)
    if french:
        month = _MONTHS.get(french.group(2).lower())
        if month:
            return datetime(int(french.group(3)), month, int(french.group(1))).date().isoformat(), False
    match = re.match(r"([A-Za-z]{3,9})\s+(\d{1,2}),\s*(\d{4})", text)
    if match:
        month = _MONTHS.get(match.group(1)[:3].lower())
        if month:
            return datetime(int(match.group(3)), month, int(match.group(2))).date().isoformat(), False
    return None, True


def parse_currency(raw: str | None) -> tuple[str | None, bool]:
    if raw is None or not str(raw).strip():
        return None, False
    text = str(raw).strip().upper()
    aliases = {
        "€": "EUR", "EURO": "EUR", "EUROS": "EUR", "DH": "MAD", "MAD": "MAD",
        "DIRHAM": "MAD", "DIRHAMS": "MAD", "USD": "USD", "EUR": "EUR", "$": "USD",
    }
    code = aliases.get(text)
    if code:
        return code, False
    if re.fullmatch(r"[A-Z]{3}", text):
        return text, text not in {"EUR", "MAD", "USD"}
    return None, True


def normalize_key(raw: str | None) -> str | None:
    if raw is None or not str(raw).strip():
        return None
    return re.sub(r"\s+", "", str(raw)).upper()


def parse_marker(raw: str | None) -> tuple[int | None, int | None]:
    if not raw:
        return None, None
    match = re.search(r"(\d+)\s*(?:of|/)\s*(\d+)", raw, re.I)
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def field_from_raw(raw: RawField, *, kind: str, document_id: str) -> FieldValue:
    source_page = None if raw.source_page in (None, 0) else raw.source_page
    if raw.raw_text is None or not str(raw.raw_text).strip():
        return FieldValue(source_document_id=document_id, source_page=source_page, status="missing")
    value: object
    ambiguous = False
    currency = None
    if kind == "money":
        value, ambiguous = parse_decimal(raw.raw_text)
        value = str(value) if value is not None else None
    elif kind == "date":
        value, ambiguous = parse_date(raw.raw_text)
    elif kind == "currency":
        value, ambiguous = parse_currency(raw.raw_text)
        currency = value if not ambiguous else None
    else:
        value = str(raw.raw_text).strip()
    if ambiguous or value is None:
        return FieldValue(
            raw_text=raw.raw_text,
            source_document_id=document_id,
            source_page=source_page,
            status="review",
        )
    status = "high" if source_page is not None else "review"
    return FieldValue(
        value=value,
        raw_text=raw.raw_text,
        currency=currency,
        source_document_id=document_id,
        source_page=source_page,
        method="normalized" if kind in {"money", "date", "currency"} else "ai",
        status=status,
    )


_KINDS = {
    "document_date": "date",
    "currency": "currency",
    "net_amount": "money",
    "tax_amount": "money",
    "total_amount": "money",
    "fob_amount": "money",
    "freight_amount": "money",
    "customs_value": "money",
    "insurance_amount": "money",
    "exchange_rate": "money",
    "quantity": "money",
    "unit_price": "money",
    "amount": "money",
}


def lines_from_raw(lines: list[RawLine], document_id: str) -> list[LineRecord]:
    records = []
    for line in lines:
        fields = {}
        for name in ("code", "description", "quantity", "unit_price", "amount"):
            fields[name] = field_from_raw(getattr(line, name), kind=_KINDS.get(name, "text"), document_id=document_id)
        records.append(LineRecord(fields=fields))
    return records
