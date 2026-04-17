from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class AccountSnapshot(BaseModel):
    account_id: str = ""
    net_liquidation: float | None = None
    available_funds: float | None = None
    buying_power: float | None = None
    currency: str = "USD"
    source: str = "unknown"
    updated_at: datetime


class PositionSnapshot(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    quantity: float
    average_cost: float | None = None
    market_price: float | None = None
    market_value: float | None = None
    unrealized_pnl: float | None = None
    unrealized_pnl_percent: float | None = None
    currency: str = "USD"
    account_id: str = ""

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()
