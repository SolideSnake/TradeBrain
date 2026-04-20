from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.preferences.models import IBKRSettings


class IBKRSettingsRepository:
    def get(self, db: Session) -> IBKRSettings | None:
        return db.scalar(select(IBKRSettings).order_by(IBKRSettings.id.asc()))

    def save(self, db: Session, settings: IBKRSettings) -> IBKRSettings:
        db.add(settings)
        return settings
