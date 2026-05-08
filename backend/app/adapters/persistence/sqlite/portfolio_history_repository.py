from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domains.portfolio_history.models import PortfolioHistoryPoint


class PortfolioHistoryRepository:
    def create(
        self,
        db: Session,
        *,
        recorded_at: datetime,
        account_id: str,
        broker_profile: str,
        currency: str,
        net_liquidation: float | None,
        cash_balance: float | None,
        available_funds: float | None,
        buying_power: float | None,
        unrealized_pnl: float | None,
        positions_market_value: float | None,
        source_snapshot_at: datetime | None,
    ) -> PortfolioHistoryPoint:
        record = PortfolioHistoryPoint(
            recorded_at=recorded_at,
            account_id=account_id,
            broker_profile=broker_profile,
            currency=currency,
            net_liquidation=net_liquidation,
            cash_balance=cash_balance,
            available_funds=available_funds,
            buying_power=buying_power,
            unrealized_pnl=unrealized_pnl,
            positions_market_value=positions_market_value,
            source_snapshot_at=source_snapshot_at,
        )
        db.add(record)
        db.flush()
        return record

    def list_since(
        self,
        db: Session,
        *,
        since: datetime,
        broker_profile: str | None,
    ) -> list[PortfolioHistoryPoint]:
        query = select(PortfolioHistoryPoint).where(PortfolioHistoryPoint.recorded_at >= since)
        if broker_profile:
            query = query.where(PortfolioHistoryPoint.broker_profile == broker_profile)
        query = query.order_by(PortfolioHistoryPoint.recorded_at.asc(), PortfolioHistoryPoint.id.asc())
        return list(db.scalars(query))

    def latest_profile(self, db: Session) -> str | None:
        return db.scalar(
            select(PortfolioHistoryPoint.broker_profile)
            .order_by(PortfolioHistoryPoint.recorded_at.desc(), PortfolioHistoryPoint.id.desc())
            .limit(1)
        )

    def prune(
        self,
        db: Session,
        *,
        retention_days: int,
        max_rows: int,
        now: datetime | None = None,
    ) -> None:
        now = now or datetime.now(timezone.utc)
        if retention_days > 0:
            cutoff = now - timedelta(days=retention_days)
            db.execute(
                delete(PortfolioHistoryPoint)
                .where(PortfolioHistoryPoint.recorded_at < cutoff)
                .execution_options(synchronize_session=False)
            )

        if max_rows <= 0:
            return

        overflow_ids = list(
            db.scalars(
                select(PortfolioHistoryPoint.id)
                .order_by(PortfolioHistoryPoint.recorded_at.desc(), PortfolioHistoryPoint.id.desc())
                .offset(max_rows)
            )
        )
        if overflow_ids:
            db.execute(
                delete(PortfolioHistoryPoint)
                .where(PortfolioHistoryPoint.id.in_(overflow_ids))
                .execution_options(synchronize_session=False)
            )
