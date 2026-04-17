from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.persistence.sqlite.db import Base
from app.core.types.common import ValuationLabel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WatchlistState(Base):
    __tablename__ = "watchlist_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    current_label: Mapped[ValuationLabel | None] = mapped_column(
        Enum(ValuationLabel, native_enum=False),
        nullable=True,
    )
    previous_label: Mapped[ValuationLabel | None] = mapped_column(
        Enum(ValuationLabel, native_enum=False),
        nullable=True,
    )
    changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
