from pydantic import BaseModel, ConfigDict, Field

from app.documents.common import RawField, RawLine
from app.models import DocumentType

PROMPT_VERSION = "1"
SCHEMA_VERSION = "1"


class ClassifyPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_number: int
    document_type: DocumentType
    title: str | None = None


class ClassifyPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pages: list[ClassifyPage]


class BoundaryPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_number: int
    document_key: str | None = None
    page_marker: str | None = None


class BoundaryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pages: list[BoundaryPage]


class MoneyDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supplier_name: RawField = RawField()
    document_number: RawField = RawField()
    document_date: RawField = RawField()
    currency: RawField = RawField()
    net_amount: RawField = RawField()
    tax_amount: RawField = RawField()
    total_amount: RawField = RawField()
    fob_amount: RawField = RawField()
    freight_amount: RawField = RawField()
    customs_value: RawField = RawField()
    exchange_rate: RawField = RawField()
    insurance_amount: RawField = RawField()
    bill_of_lading: RawField = RawField()
    containers: RawField = RawField()
    hs_code: RawField = RawField()
    package_count: RawField = RawField()
    regime: RawField = RawField()
    lines: list[RawLine] = Field(default_factory=list)


DOCUMENT_TYPES: tuple[DocumentType, ...] = (
    "supplier_invoice",
    "import_licence",
    "customs_declaration",
    "customs_liquidation",
    "carrier_invoice",
    "logistics_invoice",
    "broker_invoice",
    "unknown",
)

PROMPT_FILES = {
    "supplier_invoice": "supplier_invoice_v1.txt",
    "import_licence": "import_licence_v1.txt",
    "customs_declaration": "customs_declaration_v1.txt",
    "customs_liquidation": "customs_liquidation_v1.txt",
    "carrier_invoice": "carrier_invoice_v1.txt",
    "logistics_invoice": "logistics_invoice_v1.txt",
    "broker_invoice": "broker_invoice_v1.txt",
    "unknown": "unknown_v1.txt",
}


def schema_for(document_type: str) -> type[BaseModel]:
    if document_type in PROMPT_FILES:
        return MoneyDocument
    raise KeyError(document_type)
