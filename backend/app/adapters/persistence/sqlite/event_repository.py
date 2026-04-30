from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domains.events.models import EventRecord


class EventRepository:
    def list_recent(self, db: Session, limit: int = 50) -> list[EventRecord]:
        safe_limit = max(1, min(limit, 200))
        query = (
            select(EventRecord)
            .order_by(EventRecord.occurred_at.desc(), EventRecord.id.desc())
            .limit(safe_limit)
        )
        return list(db.scalars(query))

    def create(
        self,
        db: Session,
        *,
        event_type: str,
        source: str,
        severity: str = "info",
        title: str,
        message: str = "",
        symbol: str = "",
        status: str = "",
        entity_type: str = "",
        entity_id: str = "",
        payload: dict[str, Any] | None = None,
        occurred_at: datetime | None = None,
    ) -> EventRecord:
        record = EventRecord(
            event_type=event_type,
            source=source,
            severity=severity,
            title=title,
            message=message,
            symbol=symbol,
            status=status,
            entity_type=entity_type,
            entity_id=entity_id,
            payload_json=json.dumps(payload or {}, ensure_ascii=False),
            occurred_at=occurred_at or datetime.now(timezone.utc),
        )
        db.add(record)
        db.flush()
        return record

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
                delete(EventRecord)
                .where(EventRecord.occurred_at < cutoff)
                .execution_options(synchronize_session=False)
            )

        if max_rows <= 0:
            return

        overflow_ids = list(
            db.scalars(
                select(EventRecord.id)
                .order_by(EventRecord.occurred_at.desc(), EventRecord.id.desc())
                .offset(max_rows)
            )
        )
        if overflow_ids:
            db.execute(
                delete(EventRecord)
                .where(EventRecord.id.in_(overflow_ids))
                .execution_options(synchronize_session=False)
            )
