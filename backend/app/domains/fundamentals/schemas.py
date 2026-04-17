from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class FundamentalSnapshot(BaseModel):
    pe_ratio: float | None = None
    earnings_growth_rate_percent: float | None = None
    peg_ratio: float | None = None
    source: str = "unknown"
    as_of: datetime | None = None
