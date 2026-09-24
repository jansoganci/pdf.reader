from pydantic import BaseModel, ValidationError

from app.providers.base import AIProvider, ProviderRefusal, ProviderSuccess, ProviderTransportError


def call_structured(provider_call, model: type[BaseModel], images: list[bytes]):
    first = provider_call(images, None)
    if isinstance(first, ProviderTransportError):
        return first, None
    if isinstance(first, ProviderRefusal):
        return first, None
    assert isinstance(first, ProviderSuccess)
    try:
        return first, model.model_validate(first.payload)
    except ValidationError as exc:
        note = exc.errors()[0]["msg"] if exc.errors() else "schema mismatch"
        second = provider_call(images, note[:300])
        if not isinstance(second, ProviderSuccess):
            return second, None
        try:
            return second, model.model_validate(second.payload)
        except ValidationError as second_exc:
            return second, second_exc
