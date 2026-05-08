from __future__ import annotations

from datetime import UTC, datetime, timedelta

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlite.portfolio_history_repository import (
    PortfolioHistoryRepository,
)
from app.adapters.persistence.sqlite.snapshot_repository import SnapshotRepository
from app.domains.portfolio.schemas import PositionSnapshot
from app.domains.portfolio_history.models import PortfolioHistoryPoint
from app.domains.portfolio_history.schemas import (
    PortfolioHistoryPointRead,
    PortfolioHistoryRange,
)
from app.domains.snapshot.schemas import CanonicalSnapshot


class PortfolioHistoryService:
    def __init__(
        self,
        repository: PortfolioHistoryRepository | None = None,
        snapshot_repository: SnapshotRepository | None = None,
        retention_days: int = 365,
        max_rows: int = 100000,
        max_points: int = 500,
    ) -> None:
        self.repository = repository or PortfolioHistoryRepository()
        self.snapshot_repository = snapshot_repository or SnapshotRepository()
        self.retention_days = retention_days
        self.max_rows = max_rows
        self.max_points = max_points

    def record_snapshot(self, db: Session, snapshot: CanonicalSnapshot) -> PortfolioHistoryPoint:
        record = self.repository.create(
            db,
            recorded_at=self._as_utc_aware(datetime.now(UTC)),
            account_id=snapshot.account.account_id,
            broker_profile=snapshot.meta.broker_profile,
            currency=snapshot.account.currency,
            net_liquidation=snapshot.account.net_liquidation,
            cash_balance=snapshot.account.cash_balance,
            available_funds=snapshot.account.available_funds,
            buying_power=snapshot.account.buying_power,
            unrealized_pnl=self._sum_position_values(snapshot.positions, "unrealized_pnl_base", "unrealized_pnl"),
            positions_market_value=self._sum_position_values(snapshot.positions, "market_value_base", "market_value"),
            source_snapshot_at=self._as_utc_aware(snapshot.meta.generated_at),
        )
        self.repository.prune(
            db,
            retention_days=self.retention_days,
            max_rows=self.max_rows,
        )
        return record

    def list_history(
        self,
        db: Session,
        *,
        range_name: PortfolioHistoryRange,
    ) -> list[PortfolioHistoryPointRead]:
        profile = self._current_snapshot_profile(db) or self.repository.latest_profile(db)
        since = self._range_start(range_name)
        records = self.repository.list_since(db, since=since, broker_profile=profile)
        return [self._to_read(record) for record in self._sample(records)]

    def _current_snapshot_profile(self, db: Session) -> str | None:
        record = self.snapshot_repository.get(db)
        if not record or not record.snapshot_json:
            return None
        try:
            snapshot = CanonicalSnapshot.model_validate_json(record.snapshot_json)
        except ValidationError:
            return None
        return snapshot.meta.broker_profile

    def _range_start(self, range_name: PortfolioHistoryRange) -> datetime:
        now = datetime.now(UTC)
        if range_name == "1D":
            return now - timedelta(days=1)
        if range_name == "1W":
            return now - timedelta(days=7)
        if range_name == "1M":
            return now - timedelta(days=30)
        return datetime(now.year, 1, 1, tzinfo=UTC)

    def _sample(self, records: list[PortfolioHistoryPoint]) -> list[PortfolioHistoryPoint]:
        if len(records) <= self.max_points:
            return records
        if self.max_points <= 1:
            return records[:1]

        last_index = len(records) - 1
        selected: list[PortfolioHistoryPoint] = []
        previous_index = -1
        for index in range(self.max_points):
            record_index = round(index * last_index / (self.max_points - 1))
            if record_index != previous_index:
                selected.append(records[record_index])
                previous_index = record_index
        return selected

    def _to_read(self, record: PortfolioHistoryPoint) -> PortfolioHistoryPointRead:
        return PortfolioHistoryPointRead(
            recorded_at=self._as_utc_aware(record.recorded_at),
            account_id=record.account_id,
            broker_profile=record.broker_profile,  # type: ignore[arg-type]
            currency=record.currency,
            net_liquidation=record.net_liquidation,
            cash_balance=record.cash_balance,
            available_funds=record.available_funds,
            buying_power=record.buying_power,
            unrealized_pnl=record.unrealized_pnl,
            positions_market_value=record.positions_market_value,
        )

    def _sum_position_values(
        self,
        positions: list[PositionSnapshot],
        preferred_attr: str,
        fallback_attr: str,
    ) -> float | None:
        total = 0.0
        has_value = False
        for position in positions:
            value = getattr(position, preferred_attr)
            if value is None:
                value = getattr(position, fallback_attr)
            if value is None:
                continue
            total += value
            has_value = True
        return total if has_value else None

    def _as_utc_aware(self, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
