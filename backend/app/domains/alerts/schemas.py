from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.core.types.common import AlertChannel, AlertDeliveryStatus, AlertLevel


class AlertEventRead(BaseModel):
    id: int
    symbol: str
    channel: AlertChannel
    level: AlertLevel
    delivery_status: AlertDeliveryStatus
    title: str
    message: str
    error_detail: str
    created_at: datetime

    model_config = {"from_attributes": True}
