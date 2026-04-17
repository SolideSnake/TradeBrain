from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.preferences.models import NotificationSettings


class NotificationSettingsRepository:
    def get(self, db: Session) -> NotificationSettings | None:
        return db.scalar(select(NotificationSettings).order_by(NotificationSettings.id.asc()))

    def save(self, db: Session, settings: NotificationSettings) -> NotificationSettings:
        db.add(settings)
        return settings
