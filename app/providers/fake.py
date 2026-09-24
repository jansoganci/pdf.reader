from app.models import Usage
from app.providers.base import ProviderRefusal, ProviderResult, ProviderSuccess, ProviderTransportError


class FakeProvider:
    """Returns scripted payloads. It never invents amounts unless a test script says so."""

    def __init__(self, script: dict | None = None, fail_schema_times: int = 0, refuse: bool = False):
        self.script = script or {}
        self.fail_schema_times = fail_schema_times
        self.refuse = refuse
        self.calls: list[str] = []

    def _usage(self) -> Usage:
        return Usage(input_tokens=0, output_tokens=0, duration_ms=1)

    def _result(self, name: str, payload: dict) -> ProviderResult:
        self.calls.append(name)
        if self.refuse:
            return ProviderRefusal(usage=self._usage())
        if self.fail_schema_times > 0:
            self.fail_schema_times -= 1
            return ProviderSuccess(payload={"unexpected": True}, usage=self._usage())
        if self.script.get("transport_error"):
            return ProviderTransportError(message="temporary network failure", usage=self._usage())
        return ProviderSuccess(payload=payload, usage=self._usage())

    def classify_pages(self, images: list[bytes], note: str | None = None, page_numbers: list[int] | None = None) -> ProviderResult:
        payload = self.script.get("classify")
        if payload is None:
            payload = {
                "pages": [
                    {"page_number": index + 1, "document_type": "unknown", "title": None}
                    for index in range(len(images))
                ]
            }
        return self._result("classify", payload)

    def read_boundary_evidence(self, images: list[bytes], note: str | None = None, page_numbers: list[int] | None = None) -> ProviderResult:
        payload = self.script.get("boundary")
        if payload is None:
            payload = {
                "pages": [
                    {"page_number": index + 1, "document_key": None, "page_marker": None}
                    for index in range(len(images))
                ]
            }
        return self._result("boundary", payload)

    def extract_document(
        self,
        document_type: str,
        images: list[bytes],
        note: str | None = None,
        page_numbers: list[int] | None = None,
    ) -> ProviderResult:
        sequence = self.script.get("extract_sequence")
        if sequence:
            payload = sequence.pop(0)
        else:
            payload = self.script.get("extract", {}).get(document_type, {})
        return self._result(f"extract:{document_type}", payload)
