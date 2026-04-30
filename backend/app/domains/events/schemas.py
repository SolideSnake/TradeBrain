from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EventRecordRead(BaseModel):
    id: int
    event_type: str
    source: str
    severity: str
    title: str
    message: str
    symbol: str
    status: str
    entity_type: str
    entity_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime
    created_at: datetime
