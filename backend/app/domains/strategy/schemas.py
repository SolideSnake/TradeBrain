from __future__ import annotations

from pydantic import BaseModel, Field


class StrategyRule(BaseModel):
    id: str
    name: str
    max_peg: float | None = None
    min_drawdown_52w_percent: float | None = None
    min_day_drop_percent: float | None = None


class StrategyEvaluation(BaseModel):
    rule_id: str
    rule_name: str
    matched: bool
    reasons: list[str] = Field(default_factory=list)
