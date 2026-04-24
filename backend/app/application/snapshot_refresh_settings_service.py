from __future__ import annotations

from sqlalchemy.orm import Session

from app.adapters.persistence.sqlite.snapshot_refresh_settings_repository import (
    SnapshotRefreshSettingsRepository,
)
from app.domains.preferences.models import SnapshotRefreshSettings
from app.domains.preferences.schemas import (
    SnapshotRefreshSettingsRead,
    SnapshotRefreshSettingsUpdate,
)


class SnapshotRefreshSettingsService:
    DEFAULT_INTERVAL_SECONDS = 300
    MIN_INTERVAL_SECONDS = 300

    def __init__(self, repository: SnapshotRefreshSettingsRepository | None = None) -> None:
        self.repository = repository or SnapshotRefreshSettingsRepository()

    def get_settings(self, db: Session) -> SnapshotRefreshSettingsRead:
        stored = self.repository.get(db)
        if stored is None:
            return SnapshotRefreshSettingsRead(
                enabled=True,
                interval_seconds=self.DEFAULT_INTERVAL_SECONDS,
            )
        return self._read_from_model(stored)

    def update_settings(
        self,
        db: Session,
        payload: SnapshotRefreshSettingsUpdate,
    ) -> SnapshotRefreshSettingsRead:
        stored = self.repository.get(db)
        if stored is None:
            stored = SnapshotRefreshSettings()

        updates = payload.model_dump(exclude_unset=True)
        if "enabled" in updates:
            stored.enabled = updates["enabled"]
        if "interval_seconds" in updates and updates["interval_seconds"] is not None:
            stored.interval_seconds = updates["interval_seconds"]

        self.repository.save(db, stored)
        db.commit()
        db.refresh(stored)
        return self._read_from_model(stored)

    def _read_from_model(self, stored: SnapshotRefreshSettings) -> SnapshotRefreshSettingsRead:
        return SnapshotRefreshSettingsRead(
            enabled=stored.enabled,
            interval_seconds=max(stored.interval_seconds, self.MIN_INTERVAL_SECONDS),
        )
