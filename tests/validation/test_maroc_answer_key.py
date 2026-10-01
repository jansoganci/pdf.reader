from app.models import DocumentRecord, Dossier, FieldValue, LineRecord
from app.validation.rules import validate_dossier


def money(value: str) -> FieldValue:
    return FieldValue(value=value, raw_text=value, source_page=1, status="high", method="normalized")


def text(value: str) -> FieldValue:
    return FieldValue(value=value, raw_text=value, source_page=1, status="high")


def lines(*amounts: str) -> list[LineRecord]:
    return [LineRecord(fields={"amount": money(amount)}) for amount in amounts]


def paper(document_id: str, document_type: str, fields: dict, rows: list[LineRecord] | None = None) -> DocumentRecord:
    return DocumentRecord(
        id=document_id,
        document_type=document_type,
        page_numbers=[1],
        fields=fields,
        lines=rows or [],
    )


def test_maroc_pack_checks_pass_on_the_printed_amounts():
    broker_rows = lines("2000.00", "100.00", "450.00", "80.00", "50.00", "2500.00", "864.00")
    dossier = Dossier(
        id="maroc",
        filename="maroc-import-document.pdf",
        sha256="abc",
        pipeline_signature="sig",
        status="needs_review",
        documents=[
            paper(
                "broker",
                "broker_invoice",
                {"net_amount": money("5180.00"), "tax_amount": money("786.00"), "total_amount": money("6830.00"), "currency": text("MAD")},
                broker_rows,
            ),
            paper(
                "oncf-storage",
                "logistics_invoice",
                {
                    "document_number": text("IM26091043"),
                    "net_amount": money("120.00"),
                    "tax_amount": money("24.00"),
                    "total_amount": money("144.00"),
                    "bill_of_lading": text("274249082"),
                    "containers": text("MRSU5871618/40;MRSU7178618/40;"),
                    "currency": text("MAD"),
                },
                lines("0.00", "120.00"),
            ),
            paper(
                "oncf-weigh",
                "logistics_invoice",
                {
                    "document_number": text("IM26091161"),
                    "net_amount": money("600.00"),
                    "tax_amount": money("120.00"),
                    "total_amount": money("720.00"),
                    "bill_of_lading": text("274249082"),
                    "containers": text("MRSU5871618/40;MRSU7178618/40;"),
                    "currency": text("MAD"),
                },
                lines("600.00"),
            ),
            paper(
                "maersk",
                "carrier_invoice",
                {
                    "document_number": text("7631239091"),
                    "net_amount": money("6464.00"),
                    "tax_amount": money("332.80"),
                    "total_amount": money("6796.80"),
                    "bill_of_lading": text("274249082"),
                    "containers": text("MRSU5871618, MRSU7178618"),
                    "currency": text("MAD"),
                },
                lines("64.00", "310.00", "4090.00", "400.00", "1600.00"),
            ),
            paper(
                "dum",
                "customs_declaration",
                {
                    "document_number": text("30001020260084461"),
                    "total_amount": money("18921.090"),
                    "customs_value": money("210800.000"),
                    "bill_of_lading": text("03|30000020260014501|274249082|EGPSD|2020102481035"),
                    "containers": text("MRSU5871618;MRSU7178618"),
                    "currency": text("EUR"),
                },
                lines("210800.000"),
            ),
            paper(
                "liquidation",
                "customs_liquidation",
                {
                    "document_number": text("300001CEE20260001924"),
                    "tax_amount": money("42266.00"),
                    "total_amount": money("44004.00"),
                    "customs_value": money("210800.00"),
                    "currency": text("MAD"),
                },
                lines("0.00", "527.00", "42266.00"),
            ),
            paper(
                "supplier",
                "supplier_invoice",
                {
                    "document_number": text("EX/26/502459/1"),
                    "total_amount": money("18921.09"),
                    "fob_amount": money("16696.43"),
                    "freight_amount": money("2224.66"),
                    "containers": text("SHIPMENT NO : 3004682632 3004682634"),
                    "currency": text("EUR"),
                },
                lines("13409.76", "5511.33"),
            ),
            paper(
                "licence",
                "import_licence",
                {
                    "document_number": text("2026100000001119601"),
                    "total_amount": money("18921.09"),
                    "fob_amount": money("16696.43"),
                    "freight_amount": money("2224.66"),
                    "currency": text("EUR"),
                },
            ),
        ],
    )
    failed = [item.rule_id for item in validate_dossier(dossier) if item.status == "failed"]
    assert failed == []


def test_a_real_line_mismatch_still_fails():
    dossier = Dossier(
        id="bad-lines",
        filename="bad.pdf",
        sha256="abc",
        pipeline_signature="sig",
        status="needs_review",
        documents=[
            paper(
                "carrier",
                "carrier_invoice",
                {"net_amount": money("100.00"), "tax_amount": money("20.00"), "total_amount": money("120.00")},
                lines("50.00"),
            )
        ],
    )
    failed = [item.rule_id for item in validate_dossier(dossier) if item.status == "failed"]
    assert "lines_sum_to_total" in failed
