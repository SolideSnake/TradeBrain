from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.adapters.persistence.sqlite.event_repository import EventRepository
from app.config.settings import get_settings
from app.domains.events.models import EventRecord
from app.domains.events.schemas import EventRecordRead


class EventService:
    def __init__(
        self,
        repository: EventRepository | None = None,
        retention_days: int | None = None,
        max_rows: int | None = None,
    ) -> None:
        settings = get_settings()
        self.repository = repository or EventRepository()
        self.retention_days = (
            retention_days if retention_days is not None else settings.event_retention_days
        )
        self.max_rows = max_rows if max_rows is not None else settings.event_retention_max_rows

    def list_recent(self, db: Session, limit: int = 50) -> list[EventRecordRead]:
        return [self._to_read(record) for record in self.repository.list_recent(db, limit)]

    def record_event(
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
    ) -> EventRecordRead:
        record = self.repository.create(
            db,
            event_type=event_type,
            source=source,
            severity=severity,
            title=title,
            message=message,
            symbol=symbol,
            status=status,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            occurred_at=occurred_at,
        )
        db.flush()
        db.refresh(record)
        event = self._to_read(record)
        self.repository.prune(
            db,
            retention_days=self.retention_days,
            max_rows=self.max_rows,
        )
        return event

    def _to_read(self, record: EventRecord) -> EventRecordRead:
        try:
            payload = json.loads(record.payload_json or "{}")
        except json.JSONDecodeError:
            payload = {}

        return EventRecordRead(
            id=record.id,
            event_type=record.event_type,
            source=record.source,
            severity=record.severity,
            title=record.title,
            message=record.message,
            symbol=record.symbol,
            status=record.status,
            entity_type=record.entity_type,
            entity_id=record.entity_id,
            payload=payload if isinstance(payload, dict) else {},
            occurred_at=record.occurred_at,
            created_at=record.created_at,
        )
