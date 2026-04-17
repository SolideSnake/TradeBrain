from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.persistence.sqlite.db import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NotificationSettings(Base):
    __tablename__ = "notification_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_bot_token: Mapped[str] = mapped_column(Text, nullable=False, default="")
    telegram_chat_id: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
