from __future__ import annotations

import asyncio
from contextlib import suppress
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session, sessionmaker

from app.adapters.persistence.sqlite.db import get_session_factory
from app.adapters.persistence.sqlite.snapshot_repository import SnapshotRepository
from app.application.snapshot_cache_service import SnapshotCacheService
from app.application.snapshot_refresh_settings_service import SnapshotRefreshSettingsService


class SnapshotRefreshJob:
    def __init__(
        self,
        session_factory: sessionmaker[Session] | None = None,
        settings_service: SnapshotRefreshSettingsService | None = None,
        snapshot_cache_service: SnapshotCacheService | None = None,
        snapshot_repository: SnapshotRepository | None = None,
        poll_seconds: int = 5,
        started_at: datetime | None = None,
    ) -> None:
        self.session_factory = session_factory or get_session_factory()
        self.settings_service = settings_service or SnapshotRefreshSettingsService()
        self.snapshot_cache_service = snapshot_cache_service or SnapshotCacheService()
        self.snapshot_repository = snapshot_repository or SnapshotRepository()
        self.poll_seconds = poll_seconds
        self.started_at = started_at or datetime.now(timezone.utc)
        self._task: asyncio.Task[None] | None = None
        self._running = False

    def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._running = False
        if self._task is None:
            return
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task

    async def _run(self) -> None:
        while self._running:
            await asyncio.sleep(self.poll_seconds)
            await asyncio.to_thread(self.run_once)

    def run_once(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        with self.session_factory() as db:
            settings = self.settings_service.get_settings(db)
            if not settings.enabled:
                return False

            record = self.snapshot_repository.get(db)
            if not self._is_due(now, settings.interval_seconds, record):
                return False

            self.snapshot_cache_service.refresh(db)
            return True

    def _is_due(self, now: datetime, interval_seconds: int, record) -> bool:
        interval = timedelta(seconds=interval_seconds)
        if record is None:
            return now - self.started_at >= interval

        if getattr(record, "cache_status", "") == "refreshing":
            refresh_started_at = self._as_aware(getattr(record, "refresh_started_at", None))
            if refresh_started_at is not None and now - refresh_started_at < interval:
                return False

        if not getattr(record, "snapshot_json", ""):
            return now - self.started_at >= interval

        last_event_at = max(
            (
                value
                for value in (
                    self._as_aware(getattr(record, "last_success_at", None)),
                    self._as_aware(getattr(record, "last_error_at", None)),
                    self._as_aware(getattr(record, "refresh_started_at", None)),
                )
                if value is not None
            ),
            default=self.started_at,
        )
        return now - last_event_at >= interval

    def _as_aware(self, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
