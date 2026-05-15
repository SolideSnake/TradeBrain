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
    currency: str = "USD"
    base_currency: str = "USD"
    fx_rate_to_base: float | None = None
    last_price_base: float | None = None
    previous_close_base: float | None = None
    bid_base: float | None = None
    ask_base: float | None = None
    as_of: datetime | None = None
    source: str = "unknown"

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()
