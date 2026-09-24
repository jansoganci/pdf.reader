from app.documents.registry import ClassifyPayload
from app.extraction.structured import call_structured
from app.providers.base import ProviderRefusal
from app.providers.fake import FakeProvider


def test_schema_miss_retries_once_then_accepts():
    provider = FakeProvider(
        script={"classify": {"pages": [{"page_number": 1, "document_type": "unknown", "title": None}]}},
        fail_schema_times=1,
    )
    call, parsed = call_structured(provider.classify_pages, ClassifyPayload, [b"img"])
    assert parsed is not None
    assert provider.calls.count("classify") == 2


def test_second_schema_miss_is_not_merged():
    provider = FakeProvider(fail_schema_times=2)
    call, parsed = call_structured(provider.classify_pages, ClassifyPayload, [b"img"])
    assert parsed is not None
    assert parsed.__class__.__name__ == "ValidationError"


def test_refusal_is_not_a_schema_retry():
    provider = FakeProvider(refuse=True)
    call, parsed = call_structured(provider.classify_pages, ClassifyPayload, [b"img"])
    assert isinstance(call, ProviderRefusal)
    assert parsed is None
    assert provider.calls == ["classify"]
