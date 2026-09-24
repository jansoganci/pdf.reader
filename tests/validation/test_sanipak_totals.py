from app.models import DocumentRecord, Dossier, FieldValue, LineRecord
from app.validation.rules import validate_dossier


def money(value: str, page: int = 1) -> FieldValue:
    return FieldValue(value=value, raw_text=value, source_page=page, status="high", method="normalized")


def doc(document_id: str, document_type: str, **fields) -> DocumentRecord:
    return DocumentRecord(
        id=document_id,
        document_type=document_type,
        page_numbers=[1],
        fields={name: money(value) for name, value in fields.items()},
    )


def test_known_totals_pass_without_being_hard_coded_in_rules():
    supplier = doc(
        "s",
        "supplier_invoice",
        total_amount="18921.09",
        fob_amount="16696.43",
        freight_amount="2224.66",
        currency="EUR",
    )
    supplier.lines = [
        LineRecord(fields={"amount": money("13409.76")}),
        LineRecord(fields={"amount": money("5511.33")}),
    ]
    dossier = Dossier(
        id="1",
        filename="sample.pdf",
        sha256="abc",
        pipeline_signature="sig",
        status="needs_review",
        documents=[
            supplier,
            doc("l", "import_licence", total_amount="18921.09", currency="EUR"),
            doc("d", "customs_declaration", customs_value="210800.00", bill_of_lading="274249082", currency="MAD"),
            doc("q", "customs_liquidation", customs_value="210800.00", total_amount="44004.00", currency="MAD"),
            doc("c", "carrier_invoice", net_amount="6464.00", tax_amount="332.80", total_amount="6796.80", currency="MAD"),
            doc("o1", "logistics_invoice", document_number="IM26091043", total_amount="144.00", currency="MAD"),
            doc("o2", "logistics_invoice", document_number="IM26091161", total_amount="720.00", currency="MAD"),
            doc("b", "broker_invoice", total_amount="6830.00", currency="MAD"),
        ],
    )
    failed = [item.rule_id for item in validate_dossier(dossier) if item.status == "failed"]
    assert failed == []
