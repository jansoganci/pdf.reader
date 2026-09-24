import pytest
from pydantic import ValidationError

from app.documents.registry import ClassifyPayload, MoneyDocument


def test_money_document_rejects_extra_keys():
    with pytest.raises(ValidationError):
        MoneyDocument.model_validate({"supplier_name": {"raw_text": "A", "source_page": 1}, "gl_account": "1000"})


def test_classify_rejects_unknown_type():
    with pytest.raises(ValidationError):
        ClassifyPayload.model_validate({"pages": [{"page_number": 1, "document_type": "gl_posting", "title": None}]})


def test_money_schema_forbids_additional_properties():
    schema = MoneyDocument.model_json_schema()
    assert schema.get("additionalProperties") is False
    assert "gl_account" not in schema["properties"]
