from __future__ import annotations

from threading import Lock

from sqlalchemy.orm import Session

from app.adapters.persistence.sqlite.snapshot_repository import SnapshotRepository
from app.application.snapshot_builder import SnapshotBuilder
from app.application.snapshot_pipeline_service import SnapshotPipelineService
from app.domains.snapshot.models import SnapshotCacheRecord
from app.domains.snapshot.schemas import CanonicalSnapshot, SnapshotResponse


_REFRESH_LOCK = Lock()


class SnapshotCacheService:
    def __init__(
        self,
        repository: SnapshotRepository | None = None,
        snapshot_pipeline_service: SnapshotPipelineService | None = None,
        snapshot_builder: SnapshotBuilder | None = None,
    ) -> None:
        self.repository = repository or SnapshotRepository()
        self.snapshot_pipeline_service = snapshot_pipeline_service
        self.snapshot_builder = snapshot_builder

    def get_latest(self, db: Session) -> SnapshotResponse:
        record = self.repository.get(db)
        if record and record.snapshot_json:
            return self._build_response(record, from_cache=True)
        return self.refresh(db)

    def refresh(self, db: Session) -> SnapshotResponse:
        if not _REFRESH_LOCK.acquire(blocking=False):
            return self._build_refreshing_response(db)

        try:
            self.repository.mark_refreshing(db)
            db.commit()

            try:
                snapshot = self._snapshot_pipeline.build_snapshot(db)
            except Exception as exc:
                record = self.repository.save_failure(db, str(exc))
                db.commit()
                db.refresh(record)
                return self._build_response(record, from_cache=bool(record.snapshot_json))

            record = self.repository.save_success(db, snapshot)
            db.commit()
            db.refresh(record)
            return self._build_response(record, from_cache=False)
        finally:
            _REFRESH_LOCK.release()

    def _build_refreshing_response(self, db: Session) -> SnapshotResponse:
        record = self.repository.mark_refreshing(db)
        db.commit()
        db.refresh(record)
        return self._build_response(record, from_cache=bool(record.snapshot_json))

    def _build_response(
        self,
        record: SnapshotCacheRecord | None,
        from_cache: bool,
    ) -> SnapshotResponse:
        if record is None:
            return SnapshotResponse(cache_status="empty", from_cache=False)

        snapshot = self._parse_snapshot(record.snapshot_json)
        cache_status = record.cache_status if record.cache_status else "empty"
        if snapshot is None and cache_status == "success":
            cache_status = "empty"

        return SnapshotResponse(
            snapshot=snapshot,
            cache_status=cache_status,
            from_cache=from_cache,
            last_success_at=record.last_success_at,
            refresh_started_at=record.refresh_started_at,
            last_error_at=record.last_error_at,
            last_error=record.last_error,
        )

    def _parse_snapshot(self, snapshot_json: str) -> CanonicalSnapshot | None:
        if not snapshot_json:
            return None
        return CanonicalSnapshot.model_validate_json(snapshot_json)

    @property
    def _snapshot_pipeline(self) -> SnapshotPipelineService:
        if self.snapshot_builder is not None:
            state_engine = None
            notification_service = None
            if self.snapshot_pipeline_service is not None:
                state_engine = self.snapshot_pipeline_service.state_engine
                notification_service = self.snapshot_pipeline_service.notification_service
            return SnapshotPipelineService(
                snapshot_builder=self.snapshot_builder,
                state_engine=state_engine,
                notification_service=notification_service,
            )
        return self.snapshot_pipeline_service or SnapshotPipelineService()
