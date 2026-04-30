from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class FxRateSnapshot(BaseModel):
    from_currency: str = Field(min_length=3, max_length=3)
    to_currency: str = Field(min_length=3, max_length=3)
    rate: float
    source: str = "unknown"
    as_of: datetime

    @field_validator("from_currency", "to_currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()
