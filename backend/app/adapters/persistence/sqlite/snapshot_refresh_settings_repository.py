from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.preferences.models import SnapshotRefreshSettings


class SnapshotRefreshSettingsRepository:
    def get(self, db: Session) -> SnapshotRefreshSettings | None:
        return db.scalar(select(SnapshotRefreshSettings).order_by(SnapshotRefreshSettings.id.asc()))

    def save(
        self,
        db: Session,
        settings: SnapshotRefreshSettings,
    ) -> SnapshotRefreshSettings:
        db.add(settings)
        return settings
