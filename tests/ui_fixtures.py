"""A Maroc-like dossier for tests of the screen code.

Eight papers in the order of the sample file (docs/UI_REVIEW.md): broker invoice on
page 1, customs payment on pages 2-3 with its total flagged on page 3, two ONCF
invoices, a two-page Maersk invoice, the customs declaration, the supplier invoice,
and the import licence. The values follow tests/validation/test_maroc_answer_key.py.
"""

from app.models import DocumentRecord, Dossier, FieldValue, LineRecord
from app.validation.rules import validate_dossier

SUPPLIER = "Ekom Eczacıbaşı Dış Tic. A.Ş."


def field(value, raw=None, page=1, status="high", method="normalized") -> FieldValue:
    return FieldValue(
        value=value, raw_text=value if raw is None else raw, source_page=page, status=status, method=method
    )


def line(description, amount, page=1) -> LineRecord:
    return LineRecord(fields={"description": field(description, page=page, method="ai"), "amount": field(amount, page=page)})


def paper(document_id, document_type, pages, fields, lines=None) -> DocumentRecord:
    return DocumentRecord(
        id=document_id, document_type=document_type, page_numbers=pages, fields=fields, lines=lines or []
    )


def maroc_dossier(dossier_id="maroc", supplier_name=SUPPLIER, maersk_last_line="1600.00", flag_review=True) -> Dossier:
    """`maersk_last_line` other than 1600.00 makes the Maersk lines miss its total: one blocking error.
    `flag_review=False` reads every value cleanly, so nothing needs a check."""
    papers = [
        paper("broker", "broker_invoice", [1], {
            "supplier_name": field("Transit Trust", method="ai"), "document_number": field("2026/003654"),
            "document_date": field("2026-08-27", "27/08/2026"), "currency": field("MAD"),
            "net_amount": field("5180.00"), "tax_amount": field("786.00"),
            "total_amount": field("6830.00", status="review"),
        }, [line("Honoraire", "2000.00"), line("Ouverture dossier", "100.00"), line("Manipulation", "450.00"),
            line("Imprimés", "80.00"), line("Lettre de réserve", "50.00"), line("Transport", "2500.00"),
            line("Magasinage", "864.00")]),
        paper("liquidation", "customs_liquidation", [2, 3], {
            "document_number": field("300001CEE20260001924", page=2),
            "document_date": field("2026-09-07", "07/09/2026", page=2),
            "customs_value": field("210800.00", page=2), "tax_amount": field("42266.00", page=3),
            "total_amount": field("44004.00", page=3, status="review"), "currency": field("MAD", page=2),
        }, [line("Droits d'importation", "0.00", 3), line("Taxe parafiscale", "527.00", 3), line("TVA", "42266.00", 3)]),
        paper("oncf1", "logistics_invoice", [4], {
            "supplier_name": field("ONCF", page=4, method="ai"), "document_number": field("IM26091043", page=4),
            "currency": field("MAD", page=4), "net_amount": field("120.00", page=4),
            "tax_amount": field("24.00", page=4), "total_amount": field("144.00", page=4),
            "bill_of_lading": field("274249082", page=4),
        }, [line("Stockage", "120.00", 4)]),
        paper("oncf2", "logistics_invoice", [5], {
            "supplier_name": field("ONCF", page=5, method="ai"), "document_number": field("IM26091161", page=5),
            "currency": field("MAD", page=5), "net_amount": field("600.00", page=5),
            "tax_amount": field("120.00", page=5), "total_amount": field("720.00", page=5),
            "bill_of_lading": field("274249082", page=5),
        }, [line("Pesée", "600.00", 5)]),
        paper("maersk", "carrier_invoice", [6, 7], {
            "supplier_name": field("Maersk A/S", page=6, method="ai"), "document_number": field("7631239091", page=6),
            "document_date": field("2026-08-24", "Aug 24, 2026", page=6), "currency": field("MAD", page=6),
            "net_amount": field("6464.00", page=6), "tax_amount": field("332.80", page=6),
            "total_amount": field("6796.80", page=6, status="review"), "bill_of_lading": field("274249082", page=6),
        }, [line("Frais", "64.00", 6), line("Manutention", "310.00", 6), line("Fret", "4090.00", 6),
            line("Surcharge", "400.00", 7), line("Documentation", maersk_last_line, 7)]),
        paper("dum", "customs_declaration", [8], {
            "document_number": field("30001020260084461", page=8), "customs_value": field("210800.000", page=8),
            "currency": field("EUR", page=8), "bill_of_lading": field("274249082", page=8),
            "package_count": field("2", page=8),
        }),
        paper("supplier", "supplier_invoice", [9], {
            "supplier_name": field(supplier_name, page=9, method="ai"), "document_number": field("EX/26/502459/1", page=9),
            "currency": field("EUR", page=9), "total_amount": field("18921.09", page=9),
            "fob_amount": field("16696.43", page=9), "freight_amount": field("2224.66", page=9),
        }, [line("Product A", "13409.76", 9), line("Product B", "5511.33", 9)]),
        paper("licence", "import_licence", [10], {
            "supplier_name": field(supplier_name, page=10, method="ai"), "document_number": field("L-2026-118", page=10),
            "currency": field("EUR", page=10), "total_amount": field("18921.09", page=10),
        }),
    ]
    dossier = Dossier(
        id=dossier_id, filename="maroc-import-document.pdf", sha256=f"sha-{dossier_id}",
        pipeline_signature="test", status="needs_review", documents=papers,
    )
    if not flag_review:
        for document in dossier.documents:
            for item in document.fields.values():
                if item.status == "review":
                    item.status = "high"
    dossier.validation = validate_dossier(dossier)
    return dossier
