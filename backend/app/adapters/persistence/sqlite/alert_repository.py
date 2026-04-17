from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.alerts.models import AlertEvent


class AlertRepository:
    def list_recent(self, db: Session, limit: int = 50) -> list[AlertEvent]:
        query = select(AlertEvent).order_by(AlertEvent.created_at.desc()).limit(limit)
        return list(db.scalars(query))

    def create(self, db: Session, **payload) -> AlertEvent:
        event = AlertEvent(**payload)
        db.add(event)
        return event
