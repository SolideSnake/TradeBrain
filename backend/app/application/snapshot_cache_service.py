from __future__ import annotations

from sqlalchemy.orm import Session

from app.adapters.persistence.sqlite.snapshot_repository import SnapshotRepository
from app.application.snapshot_builder import SnapshotBuilder
from app.domains.snapshot.models import SnapshotCacheRecord
from app.domains.snapshot.schemas import CanonicalSnapshot, SnapshotResponse


class SnapshotCacheService:
    def __init__(
        self,
        repository: SnapshotRepository | None = None,
        snapshot_builder: SnapshotBuilder | None = None,
    ) -> None:
        self.repository = repository or SnapshotRepository()
        self.snapshot_builder = snapshot_builder

    def get_latest(self, db: Session) -> SnapshotResponse:
        record = self.repository.get(db)
        if record and record.snapshot_json:
            return self._build_response(record, from_cache=True)
        return self.refresh(db)

    def refresh(self, db: Session) -> SnapshotResponse:
        self.repository.mark_refreshing(db)
        db.commit()

        try:
            snapshot = self._snapshot_builder.build(db)
        except Exception as exc:
            record = self.repository.save_failure(db, str(exc))
            db.commit()
            db.refresh(record)
            return self._build_response(record, from_cache=bool(record.snapshot_json))

        record = self.repository.save_success(db, snapshot)
        db.commit()
        db.refresh(record)
        return self._build_response(record, from_cache=False)

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
    def _snapshot_builder(self) -> SnapshotBuilder:
        return self.snapshot_builder or SnapshotBuilder()
