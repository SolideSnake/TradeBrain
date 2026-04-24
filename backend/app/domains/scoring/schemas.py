from __future__ import annotations

from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    name: str
    score: float
    reason: str


class ScoreResult(BaseModel):
    symbol: str
    score: float = Field(ge=0, le=100)
    breakdown: list[ScoreBreakdown] = Field(default_factory=list)
