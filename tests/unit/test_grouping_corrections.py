import fitz

from app.providers.fake import FakeProvider
from app.service import merge_document, process_upload, split_document
from app.storage import db


def _raw(text, page):
    return {"raw_text": text, "source_page": page}


def _doc(number, page, total):
    payload = {name: _raw(None, None) for name in (
        "supplier_name", "document_number", "document_date", "currency", "net_amount", "tax_amount",
        "total_amount", "fob_amount", "freight_amount", "customs_value", "exchange_rate",
        "insurance_amount", "bill_of_lading", "containers", "hs_code", "package_count", "regime",
    )}
    payload["lines"] = []
    payload["document_number"] = _raw(number, page)
    payload["total_amount"] = _raw(total, page)
    payload["currency"] = _raw("MAD", page)
    return payload


def test_merge_and_split_do_not_call_the_provider_again():
    pdf = fitz.open()
    pdf.new_page()
    pdf.new_page()
    data = pdf.tobytes()
    pdf.close()
    script = {
        "classify": {
            "pages": [
                {"page_number": 1, "document_type": "carrier_invoice", "title": None},
                {"page_number": 2, "document_type": "carrier_invoice", "title": None},
            ]
        },
        "boundary": {
            "pages": [
                {"page_number": 1, "document_key": "A", "page_marker": None},
                {"page_number": 2, "document_key": "B", "page_marker": None},
            ]
        },
        "extract_sequence": [
            _doc("A", 1, "10.00"),
            _doc("B", 2, "20.00"),
        ],
    }
    provider = FakeProvider(script)
    dossier = process_upload(data, "two.pdf", provider)
    calls = list(provider.calls)
    assert len(dossier.documents) == 2
    merged = merge_document(dossier.id, dossier.documents[1].id)
    assert provider.calls == calls
    assert len(merged.documents) == 1
    assert merged.documents[0].page_numbers == [1, 2]
    assert merged.documents[0].fields["total_amount"].value == "10.00"
    with db.connect() as connection:
        original = connection.execute(
            "SELECT normalized_json FROM extraction_runs WHERE dossier_id = ?",
            (dossier.id,),
        ).fetchone()
    saved = __import__("json").loads(original["normalized_json"])
    assert len(saved["documents"]) == 2
    split = split_document(dossier.id, merged.documents[0].id, 1)
    assert provider.calls == calls
    assert [document.page_numbers for document in split.documents] == [[1], [2]]
    assert split.documents[0].fields["document_number"].value == "A"
    assert split.documents[1].fields["document_number"].value == "B"
