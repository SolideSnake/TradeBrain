from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.persistence.sqlite.db import Base
from app.core.types.common import AssetType, Market


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WatchlistEntry(Base):
    __tablename__ = "watchlist_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    market: Mapped[Market] = mapped_column(
        Enum(Market, native_enum=False), nullable=False, default=Market.US
    )
    asset_type: Mapped[AssetType] = mapped_column(
        Enum(AssetType, native_enum=False), nullable=False, default=AssetType.STOCK
    )
    group_name: Mapped[str] = mapped_column(String(64), nullable=False, default="default")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    in_position: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

