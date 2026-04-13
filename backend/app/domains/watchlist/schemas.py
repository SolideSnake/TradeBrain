from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.types.common import AssetType, Market


class WatchlistEntryBase(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    market: Market = Market.US
    asset_type: AssetType = AssetType.STOCK
    group_name: str = Field(default="default", min_length=1, max_length=64)
    enabled: bool = True
    in_position: bool = False
    notes: str = ""

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("name", "group_name", "notes")
    @classmethod
    def trim_text(cls, value: str) -> str:
        return value.strip()


class WatchlistEntryCreate(WatchlistEntryBase):
    pass


class WatchlistEntryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    market: Market | None = None
    asset_type: AssetType | None = None
    group_name: str | None = Field(default=None, min_length=1, max_length=64)
    enabled: bool | None = None
    in_position: bool | None = None
    notes: str | None = None


class WatchlistEntryRead(WatchlistEntryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
