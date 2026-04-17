from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.persistence.sqlite.db import Base
from app.core.types.common import AlertChannel, AlertDeliveryStatus, AlertLevel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    channel: Mapped[AlertChannel] = mapped_column(
        Enum(AlertChannel, native_enum=False),
        nullable=False,
        default=AlertChannel.TELEGRAM,
    )
    level: Mapped[AlertLevel] = mapped_column(
        Enum(AlertLevel, native_enum=False),
        nullable=False,
        default=AlertLevel.INFO,
    )
    delivery_status: Mapped[AlertDeliveryStatus] = mapped_column(
        Enum(AlertDeliveryStatus, native_enum=False),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    error_detail: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
