from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

FieldStatus = Literal["high", "review", "missing"]
Method = Literal["ai", "normalized", "user"]
DocumentType = Literal[
    "supplier_invoice",
    "import_licence",
    "customs_declaration",
    "customs_liquidation",
    "carrier_invoice",
    "logistics_invoice",
    "broker_invoice",
    "unknown",
]


class FieldValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: Any = None
    raw_text: str | None = None
    currency: str | None = None
    source_document_id: str | None = None
    source_page: int | None = None
    method: Method = "ai"
    status: FieldStatus = "missing"
    user_value: Any = None
    user_raw_note: str | None = None


class LineRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fields: dict[str, FieldValue]


class ValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str
    severity: Literal["error", "warning"]
    status: Literal["passed", "failed"]
    fields: list[str] = Field(default_factory=list)
    expected: str | None = None
    actual: str | None = None
    message: str


class PageEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_number: int
    document_type: DocumentType
    document_key_raw: str | None = None
    document_key: str | None = None
    page_marker_raw: str | None = None
    marker_current: int | None = None
    marker_count: int | None = None
    starts_new_document: bool = True
    boundary_reason: str = "first_page"
    boundary_status: Literal["high", "review"] = "high"


class DocumentRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    document_type: DocumentType
    page_numbers: list[int]
    review_reason: str | None = None
    fields: dict[str, FieldValue]
    lines: list[LineRecord] = Field(default_factory=list)
    boundary: list[PageEvidence] = Field(default_factory=list)
    held_extractions: list["DocumentRecord"] = Field(default_factory=list)


class Usage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    duration_ms: int = 0


class Dossier(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    filename: str
    sha256: str
    pipeline_signature: str
    status: str
    documents: list[DocumentRecord]
    validation: list[ValidationResult] = Field(default_factory=list)
    manual: dict[str, str] = Field(default_factory=dict)
    export_with_errors: bool = False
    usage: Usage = Field(default_factory=Usage)
    estimated_cost_usd: float = 0.0
