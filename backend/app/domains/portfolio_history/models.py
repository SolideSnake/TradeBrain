from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.persistence.sqlite.db import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PortfolioHistoryPoint(Base):
    __tablename__ = "portfolio_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        index=True,
    )
    account_id: Mapped[str] = mapped_column(String(64), nullable=False, default="", index=True)
    broker_profile: Mapped[str] = mapped_column(String(16), nullable=False, default="paper", index=True)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    net_liquidation: Mapped[float | None] = mapped_column(Float)
    cash_balance: Mapped[float | None] = mapped_column(Float)
    available_funds: Mapped[float | None] = mapped_column(Float)
    buying_power: Mapped[float | None] = mapped_column(Float)
    unrealized_pnl: Mapped[float | None] = mapped_column(Float)
    positions_market_value: Mapped[float | None] = mapped_column(Float)
    source_snapshot_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        index=True,
    )
