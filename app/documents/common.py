from pydantic import BaseModel, ConfigDict


class RawField(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_text: str | None = None
    source_page: int | None = None


class RawLine(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: RawField = RawField()
    description: RawField = RawField()
    quantity: RawField = RawField()
    unit_price: RawField = RawField()
    amount: RawField = RawField()
