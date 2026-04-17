from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.core.types.common import ValuationLabel


class WatchlistStateSnapshot(BaseModel):
    symbol: str
    current_label: ValuationLabel | None = None
    previous_label: ValuationLabel | None = None
    has_changed: bool = False
    changed_at: datetime | None = None
    evaluated_at: datetime


class WatchlistStateRead(WatchlistStateSnapshot):
    id: int

    model_config = {"from_attributes": True}
