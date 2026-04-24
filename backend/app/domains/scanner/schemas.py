from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.core.types.common import ScannerCandidateReason
from app.domains.scoring.schemas import ScoreResult
from app.domains.strategy.schemas import StrategyEvaluation


class ScannerCandidate(BaseModel):
    symbol: str
    name: str
    reason: ScannerCandidateReason
    score: ScoreResult
    strategy: StrategyEvaluation


class ScannerResult(BaseModel):
    generated_at: datetime
    candidates: list[ScannerCandidate] = Field(default_factory=list)
