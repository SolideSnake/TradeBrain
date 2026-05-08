from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class TargetPositionBase(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    target_value_usd: float = Field(gt=0)
    notes: str = Field(default="", max_length=1000)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("notes")
    @classmethod
    def trim_notes(cls, value: str) -> str:
        return value.strip()


class TargetPositionCreate(TargetPositionBase):
    pass


class TargetPositionUpdate(BaseModel):
    symbol: str | None = Field(default=None, min_length=1, max_length=32)
    target_value_usd: float | None = Field(default=None, gt=0)
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str | None) -> str | None:
        return value.strip().upper() if value is not None else value

    @field_validator("notes")
    @classmethod
    def trim_notes(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else value


class TargetPositionRead(TargetPositionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

