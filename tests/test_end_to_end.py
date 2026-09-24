import fitz

from app.service import correct_field, export_dossier, process_upload
from app.providers.fake import FakeProvider


def _raw(text, page):
    return {"raw_text": text, "source_page": page}


def _doc(**fields):
    payload = {name: _raw(None, None) for name in (
        "supplier_name", "document_number", "document_date", "currency", "net_amount", "tax_amount",
        "total_amount", "fob_amount", "freight_amount", "customs_value", "exchange_rate",
        "insurance_amount", "bill_of_lading", "containers", "hs_code", "package_count", "regime",
    )}
    payload["lines"] = []
    for name, value in fields.items():
        if name == "lines":
            payload["lines"] = value
        else:
            text, page = value
            payload[name] = _raw(text, page)
    return payload


def _line(amount, page):
    return {
        "code": _raw(None, None),
        "description": _raw(None, None),
        "quantity": _raw(None, None),
        "unit_price": _raw(None, None),
        "amount": _raw(amount, page),
    }


def test_fixture_dossier_exports_and_keeps_the_original_after_correction(tmp_path, monkeypatch):
    pdf = fitz.open()
    for _ in range(8):
        pdf.new_page()
    data = pdf.tobytes()
    pdf.close()
    types = [
        "supplier_invoice",
        "import_licence",
        "customs_declaration",
        "customs_liquidation",
        "carrier_invoice",
        "carrier_invoice",
        "logistics_invoice",
        "logistics_invoice",
    ]
    script = {
        "classify": {"pages": [{"page_number": i + 1, "document_type": types[i], "title": None} for i in range(8)]},
        "boundary": {
            "pages": [
                {"page_number": 1, "document_key": "EX/26/502459/1", "page_marker": None},
                {"page_number": 2, "document_key": "2026100000001119601", "page_marker": None},
                {"page_number": 3, "document_key": "30001020260084461", "page_marker": None},
                {"page_number": 4, "document_key": "300001CEE20260001924", "page_marker": None},
                {"page_number": 5, "document_key": "7631239091", "page_marker": "page 1 of 2"},
                {"page_number": 6, "document_key": "7631239091", "page_marker": "page 2 of 2"},
                {"page_number": 7, "document_key": "IM26091043", "page_marker": None},
                {"page_number": 8, "document_key": "IM26091161", "page_marker": None},
            ]
        },
        "extract_sequence": [
            _doc(document_number=("EX/26/502459/1", 1), total_amount=("18921.09", 1), fob_amount=("16696.43", 1), freight_amount=("2224.66", 1), currency=("EUR", 1), lines=[_line("13409.76", 1), _line("5511.33", 1)]),
            _doc(document_number=("2026100000001119601", 2), total_amount=("18921.09", 2), currency=("EUR", 2)),
            _doc(document_number=("30001020260084461", 3), customs_value=("210800.00", 3), bill_of_lading=("274249082", 3), currency=("MAD", 3)),
            _doc(document_number=("300001CEE20260001924", 4), customs_value=("210800.00", 4), total_amount=("44004.00", 4), currency=("MAD", 4)),
            _doc(document_number=("7631239091", 5), net_amount=("6464.00", 5), tax_amount=("332.80", 5), total_amount=("6796.80", 5), currency=("MAD", 5)),
            _doc(document_number=("IM26091043", 7), total_amount=("144.00", 7), currency=("MAD", 7)),
            _doc(document_number=("IM26091161", 8), total_amount=("720.00", 8), currency=("MAD", 8)),
        ],
    }
    provider = FakeProvider(script)
    first = process_upload(data, "sample.pdf", provider)
    assert [document.document_type for document in first.documents] == [
        "supplier_invoice",
        "import_licence",
        "customs_declaration",
        "customs_liquidation",
        "carrier_invoice",
        "logistics_invoice",
        "logistics_invoice",
    ]
    assert len(first.documents[4].page_numbers) == 2
    assert first.documents[0].fields["total_amount"].value == "18921.09"
    again = process_upload(data, "sample.pdf", FakeProvider())
    assert again.id == first.id
    assert provider.calls  # first run called the scripted provider
    corrected = correct_field(first.id, first.documents[0].id, "total_amount", "1.00")
    assert corrected.documents[0].fields["total_amount"].value == "18921.09"
    assert corrected.documents[0].fields["total_amount"].user_value == "1.00"
    mark = __import__("app.service", fromlist=["mark_export_with_errors"]).mark_export_with_errors
    mark(first.id, True)
    path = export_dossier(first.id, "json")
    assert path.exists()
    fields = export_dossier(first.id, "fields_csv")
    assert "18921.09" in fields.read_text()
