import json
import sys
import types

from app.config import settings
from app.extraction.structured import call_structured
from app.documents.registry import ClassifyPayload
from app.providers.anthropic import AnthropicProvider
from app.providers.base import ProviderRefusal, ProviderTransportError


class _Usage:
    input_tokens = 3
    output_tokens = 4
    cache_creation_input_tokens = 0
    cache_read_input_tokens = 0


class _Block:
    type = "text"

    def __init__(self, text):
        self.text = text


class _Response:
    def __init__(self, text, stop_reason="end_turn"):
        self.content = [_Block(text)]
        self.stop_reason = stop_reason
        self.usage = _Usage()


class _Status(Exception):
    def __init__(self):
        super().__init__("nope")
        self.status_code = 429


def _install(monkeypatch, response=None, error=None):
    calls = []

    class Messages:
        def create(self, **kwargs):
            calls.append(kwargs)
            if error:
                raise error
            return response

    class Client:
        def __init__(self, **kwargs):
            self.messages = Messages()

    module = types.ModuleType("anthropic")
    module.Anthropic = Client
    module.APIStatusError = _Status
    module.APIConnectionError = type("APIConnectionError", (Exception,), {})
    module.APITimeoutError = type("APITimeoutError", (Exception,), {})
    monkeypatch.setitem(sys.modules, "anthropic", module)
    monkeypatch.setattr(settings, "live_extraction", "1")
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")
    monkeypatch.setattr(settings, "anthropic_model", "claude-sonnet-5")
    monkeypatch.setattr(settings, "anthropic_effort", "medium")
    return calls


def test_adapter_sends_model_effort_system_and_images_before_text(monkeypatch):
    payload = {"pages": [{"page_number": 1, "document_type": "unknown", "title": None}]}
    calls = _install(monkeypatch, _Response(json.dumps(payload)))
    provider = AnthropicProvider()
    result = provider.classify_pages([b"jpeg-bytes"])
    sent = calls[0]
    assert sent["model"] == "claude-sonnet-5"
    assert sent["output_config"]["effort"] == "medium"
    assert sent["output_config"]["format"]["type"] == "json_schema"
    assert "untrusted data" in sent["system"]
    assert "tools" not in sent
    assert "temperature" not in sent
    assert sent["messages"][0]["content"][0]["type"] == "image"
    assert sent["messages"][0]["content"][-1]["type"] == "text"
    assert result.payload["pages"][0]["document_type"] == "unknown"


def test_refusal_is_not_parsed_as_json(monkeypatch):
    calls = _install(monkeypatch, _Response("no", stop_reason="refusal"))
    result = AnthropicProvider().classify_pages([b"jpeg-bytes"])
    assert isinstance(result, ProviderRefusal)
    assert len(calls) == 1


def test_http_error_is_transport_and_schema_retry_is_separate(monkeypatch):
    calls = _install(monkeypatch, error=_Status())
    provider = AnthropicProvider()
    result = provider.classify_pages([b"jpeg-bytes"])
    assert isinstance(result, ProviderTransportError)
    call, parsed = call_structured(provider.classify_pages, ClassifyPayload, [b"jpeg-bytes"])
    assert isinstance(call, ProviderTransportError)
    assert parsed is None
    assert len(calls) == 2
