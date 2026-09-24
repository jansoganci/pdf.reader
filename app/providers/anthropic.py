import json
import time
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
    """Anthropic rejects Pydantic's $ref and anyOf form as too complex."""
    schema = model.model_json_schema()
    defs = schema.pop("$defs", {})

    def walk(node):
        if isinstance(node, list):
            return [walk(item) for item in node]
        if not isinstance(node, dict):
            return node
        if "$ref" in node:
            name = node["$ref"].rsplit("/", 1)[-1]
            return walk(defs[name])
        if "anyOf" in node:
            options = [walk(item) for item in node["anyOf"]]
            non_null = [item for item in options if item.get("type") != "null"]
            if len(non_null) == 1:
                return non_null[0]
            return {"type": "string"}
        cleaned = {}
        for key, value in node.items():
            if key in {"title", "default"}:
                continue
            cleaned[key] = walk(value)
        if cleaned.get("type") == "object":
            cleaned["additionalProperties"] = False
            cleaned["required"] = list(cleaned.get("properties", {}))
        if isinstance(cleaned.get("type"), list):
            types = [item for item in cleaned["type"] if item != "null"]
            cleaned["type"] = types[0] if types else "string"
        return cleaned

    flat = walk(schema)
    flat["additionalProperties"] = False
    return flat


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

    def classify_pages(self, images: list[bytes], note: str | None = None, page_numbers: list[int] | None = None) -> ProviderResult:
        return self._send(images, _prompt("classify_v1.txt"), ClassifyPayload, note, 4096, page_numbers)

    def read_boundary_evidence(self, images: list[bytes], note: str | None = None, page_numbers: list[int] | None = None) -> ProviderResult:
        return self._send(images, _prompt("boundary_v1.txt"), BoundaryPayload, note, 4096, page_numbers)

    def extract_document(
        self,
        document_type: str,
        images: list[bytes],
        note: str | None = None,
        page_numbers: list[int] | None = None,
    ) -> ProviderResult:
        filename = PROMPT_FILES[document_type]
        return self._send(images, _prompt(filename), schema_for(document_type), note, 8192, page_numbers)

    def _send(
        self,
        images: list[bytes],
        instruction: str,
        model: type[BaseModel],
        note: str | None,
        max_tokens: int,
        page_numbers: list[int] | None = None,
    ) -> ProviderResult:
        content: list[dict] = []
        for image in images:
            content.append(
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/jpeg", "data": _b64(image)},
                }
            )
        numbers = page_numbers or list(range(1, len(images) + 1))
        mapping = ", ".join(f"image {index} is source page {page}" for index, page in enumerate(numbers, start=1))
        order = (
            f"There are {len(images)} images. {mapping}. "
            "The schema does not allow null. Use an empty string and source page 0 when a value is not printed."
        )
        text = f"{instruction}\n{order}"
        if note:
            text = f"{text}\nThe previous response did not match the schema: {note}"
        content.append({"type": "text", "text": text})
        started = time.perf_counter()
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
        usage.duration_ms = int((time.perf_counter() - started) * 1000)
        stop_reason = getattr(response, "stop_reason", None)
        if stop_reason == "refusal":
            return ProviderRefusal(usage=usage)
        if stop_reason == "max_tokens":
            return ProviderSuccess(payload={"truncated": True}, usage=usage)
        text_blocks = [block.text for block in response.content if getattr(block, "type", None) == "text"]
        if not text_blocks:
            return ProviderSuccess(payload={}, usage=usage)
        try:
            payload = json.loads(text_blocks[-1])
        except json.JSONDecodeError:
            return ProviderSuccess(payload={"malformed": True}, usage=usage)
        if not isinstance(payload, dict):
            return ProviderSuccess(payload={"malformed": True}, usage=usage)
        return ProviderSuccess(payload=payload, usage=usage)


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
