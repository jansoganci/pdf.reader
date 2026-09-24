import json
from pathlib import Path

from pydantic import BaseModel

from app.config import ROOT, settings
from app.documents.registry import PROMPT_FILES, schema_for
from app.documents.registry import BoundaryPayload, ClassifyPayload
from app.models import Usage
from app.providers.base import ProviderRefusal, ProviderResult, ProviderSuccess, ProviderTransportError

_SYSTEM = (ROOT / "prompts" / "system_v1.txt").read_text(encoding="utf-8")


def _prompt(name: str) -> str:
    return (ROOT / "prompts" / name).read_text(encoding="utf-8")


def _schema(model: type[BaseModel]) -> dict:
    schema = model.model_json_schema()
    schema["additionalProperties"] = False
    return schema


class AnthropicProvider:
    """The only module that talks to the Anthropic SDK."""

    def __init__(self) -> None:
        if not settings.live_calls_allowed:
            raise RuntimeError("Live Anthropic calls are disabled. Set LIVE_EXTRACTION=1 only after approval.")
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is missing.")
        import anthropic

        self._anthropic = anthropic
        self._client = anthropic.Anthropic(
            api_key=settings.anthropic_api_key,
            timeout=settings.anthropic_timeout_seconds,
            max_retries=1,
        )

    def classify_pages(self, images: list[bytes], note: str | None = None) -> ProviderResult:
        return self._send(images, _prompt("classify_v1.txt"), ClassifyPayload, note, 4096)

    def read_boundary_evidence(self, images: list[bytes], note: str | None = None) -> ProviderResult:
        return self._send(images, _prompt("boundary_v1.txt"), BoundaryPayload, note, 4096)

    def extract_document(self, document_type: str, images: list[bytes], note: str | None = None) -> ProviderResult:
        filename = PROMPT_FILES[document_type]
        return self._send(images, _prompt(filename), schema_for(document_type), note, 8192)

    def _send(self, images: list[bytes], instruction: str, model: type[BaseModel], note: str | None, max_tokens: int) -> ProviderResult:
        content: list[dict] = []
        for image in images:
            content.append(
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/jpeg", "data": _b64(image)},
                }
            )
        text = instruction if not note else f"{instruction}\nThe previous response did not match the schema: {note}"
        content.append({"type": "text", "text": text})
        try:
            response = self._client.messages.create(
                model=settings.anthropic_model,
                max_tokens=max_tokens,
                system=_SYSTEM,
                output_config={
                    "effort": settings.anthropic_effort,
                    "format": {"type": "json_schema", "schema": _schema(model)},
                },
                messages=[{"role": "user", "content": content}],
            )
        except self._anthropic.APIStatusError as exc:
            return ProviderTransportError(message=f"HTTP {exc.status_code}", usage=Usage())
        except self._anthropic.APIConnectionError:
            return ProviderTransportError(message="temporary network failure", usage=Usage())
        except self._anthropic.APITimeoutError:
            return ProviderTransportError(message="timeout", usage=Usage())
        usage = _usage(response)
        if getattr(response, "stop_reason", None) == "refusal":
            return ProviderRefusal(usage=usage)
        text_blocks = [block.text for block in response.content if getattr(block, "type", None) == "text"]
        if not text_blocks:
            return ProviderSuccess(payload={}, usage=usage)
        return ProviderSuccess(payload=json.loads(text_blocks[-1]), usage=usage)


def _b64(image: bytes) -> str:
    import base64

    return base64.standard_b64encode(image).decode("ascii")


def _usage(response) -> Usage:
    raw = response.usage
    return Usage(
        input_tokens=getattr(raw, "input_tokens", 0) or 0,
        output_tokens=getattr(raw, "output_tokens", 0) or 0,
        cache_creation_input_tokens=getattr(raw, "cache_creation_input_tokens", 0) or 0,
        cache_read_input_tokens=getattr(raw, "cache_read_input_tokens", 0) or 0,
    )
