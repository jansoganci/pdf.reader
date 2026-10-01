from app.export.writers import fields_csv
from app.models import DocumentRecord, Dossier, FieldValue, LineRecord
from app.service import get_dossier, set_manual
from app.storage import db
from app.ui.words import shown_keys


def test_manual_boxes_stay_empty_until_typed():
    dossier = Dossier(
        id="manual-1",
        filename="sample.pdf",
        sha256="abc",
        pipeline_signature="sig",
        status="needs_review",
        documents=[
            DocumentRecord(
                id="customs",
                document_type="customs_liquidation",
                page_numbers=[2],
                fields={"document_number": FieldValue(value="300001CEE20260001924", status="high")},
            )
        ],
    )
    db.save_dossier(dossier)
    assert get_dossier("manual-1").manual == {}
    saved = set_manual("manual-1", {"order_number": "400000011470", "customs:tax_code": "   "})
    assert saved.manual == {"order_number": "400000011470"}
    assert "tax_code" not in saved.manual
    text = fields_csv(saved)
    assert "400000011470" in text
    assert "159220010" not in text


def test_broker_line_codes_stay_empty_until_typed_then_export():
    dossier = Dossier(
        id="manual-2",
        filename="sample.pdf",
        sha256="abc",
        pipeline_signature="sig",
        status="needs_review",
        documents=[
            DocumentRecord(
                id="broker",
                document_type="broker_invoice",
                page_numbers=[1],
                fields={"supplier_name": FieldValue(value="TRANSIT TRUST", status="high")},
                lines=[
                    LineRecord(fields={"description": FieldValue(value="HONORAIRE", status="high")}),
                    LineRecord(fields={"description": FieldValue(value="TRANSPORT 10%", status="high")}),
                ],
            )
        ],
    )
    db.save_dossier(dossier)
    assert get_dossier("manual-2").manual == {}

    text_before = fields_csv(get_dossier("manual-2"))
    assert "GK" not in text_before

    saved = set_manual(
        "manual-2",
        {
            "broker:line:1:tax_code": "JE",
            "broker:line:1:reason_code": "GK",
            "broker:line:2:tax_code": "  ",
        },
    )
    assert saved.manual == {"broker:line:1:tax_code": "JE", "broker:line:1:reason_code": "GK"}
    assert "broker:line:2:tax_code" not in saved.manual

    text_after = fields_csv(saved)
    assert "JE" in text_after
    assert "GK" in text_after


def test_empty_copy_fields_stay_on_screen():
    document = DocumentRecord(
        id="supplier",
        document_type="supplier_invoice",
        page_numbers=[9],
        fields={
            "supplier_name": FieldValue(status="missing"),
            "document_number": FieldValue(status="missing"),
            "total_amount": FieldValue(value="18921.09", status="high"),
        },
    )
    keys = shown_keys(document)
    assert keys[:2] == ["supplier_name", "document_number"]
    assert "total_amount" in keys
