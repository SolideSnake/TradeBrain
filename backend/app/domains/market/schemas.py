from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class QuoteSnapshot(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    last_price: float | None = None
    previous_close: float | None = None
    change_percent: float | None = None
    bid: float | None = None
    ask: float | None = None
    as_of: datetime | None = None
    source: str = "unknown"

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()
