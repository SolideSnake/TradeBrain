from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.persistence.sqlite.db import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NotificationSettings(Base):
    __tablename__ = "notification_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_bot_token: Mapped[str] = mapped_column(Text, nullable=False, default="")
    telegram_chat_id: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    feishu_webhook_url: Mapped[str] = mapped_column(Text, nullable=False, default="")
    feishu_secret: Mapped[str] = mapped_column(Text, nullable=False, default="")
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


class IBKRSettings(Base):
    __tablename__ = "ibkr_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mode: Mapped[str] = mapped_column(String(16), nullable=False, default="mock")
    active_profile: Mapped[str] = mapped_column(String(16), nullable=False, default="paper")
    real_host: Mapped[str] = mapped_column(String(128), nullable=False, default="127.0.0.1")
    real_port: Mapped[int] = mapped_column(Integer, nullable=False, default=7496)
    real_client_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    real_account_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    paper_host: Mapped[str] = mapped_column(String(128), nullable=False, default="127.0.0.1")
    paper_port: Mapped[int] = mapped_column(Integer, nullable=False, default=7497)
    paper_client_id: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    paper_account_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
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


class SnapshotRefreshSettings(Base):
    __tablename__ = "snapshot_refresh_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
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
