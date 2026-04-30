from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.fx.models import FxRateRecord
from app.domains.fx.schemas import FxRateSnapshot


class FxRateRepository:
    def upsert(self, db: Session, rate: FxRateSnapshot) -> FxRateRecord:
        now = datetime.now(UTC)
        record = db.execute(
            select(FxRateRecord).where(
                FxRateRecord.from_currency == rate.from_currency,
                FxRateRecord.to_currency == rate.to_currency,
            )
        ).scalar_one_or_none()

        if record is None:
            record = FxRateRecord(
                from_currency=rate.from_currency,
                to_currency=rate.to_currency,
                rate=rate.rate,
                source=rate.source,
                as_of=rate.as_of,
                updated_at=now,
            )
            db.add(record)
            return record

        record.rate = rate.rate
        record.source = rate.source
        record.as_of = rate.as_of
        record.updated_at = now
        return record

    def get_recent(
        self,
        db: Session,
        from_currency: str,
        to_currency: str,
        max_age: timedelta,
    ) -> FxRateSnapshot | None:
        normalized_from = from_currency.strip().upper()
        normalized_to = to_currency.strip().upper()
        record = db.execute(
            select(FxRateRecord).where(
                FxRateRecord.from_currency == normalized_from,
                FxRateRecord.to_currency == normalized_to,
            )
        ).scalar_one_or_none()

        if record is None:
            return None

        now = datetime.now(UTC)
        as_of = record.as_of
        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=UTC)
        if now - as_of > max_age:
            return None

        return FxRateSnapshot(
            from_currency=record.from_currency,
            to_currency=record.to_currency,
            rate=record.rate,
            source=record.source,
            as_of=as_of,
        )
