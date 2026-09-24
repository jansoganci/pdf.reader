from dataclasses import dataclass
from typing import Protocol

from app.models import Usage


@dataclass
class ProviderSuccess:
    payload: dict
    usage: Usage


@dataclass
class ProviderRefusal:
    usage: Usage
    reason: str = "refusal"


@dataclass
class ProviderTransportError:
    message: str
    usage: Usage


ProviderResult = ProviderSuccess | ProviderRefusal | ProviderTransportError


class AIProvider(Protocol):
    def classify_pages(self, images: list[bytes], note: str | None = None) -> ProviderResult: ...

    def read_boundary_evidence(self, images: list[bytes], note: str | None = None) -> ProviderResult: ...

    def extract_document(
        self,
        document_type: str,
        images: list[bytes],
        note: str | None = None,
    ) -> ProviderResult: ...
