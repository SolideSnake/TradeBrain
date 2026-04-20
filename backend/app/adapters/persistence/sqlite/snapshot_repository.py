from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.snapshot.models import SnapshotCacheRecord
from app.domains.snapshot.schemas import CanonicalSnapshot


class SnapshotRepository:
    def get(self, db: Session) -> SnapshotCacheRecord | None:
        return db.scalar(select(SnapshotCacheRecord).order_by(SnapshotCacheRecord.id.asc()))

    def get_or_create(self, db: Session) -> SnapshotCacheRecord:
        record = self.get(db)
        if record is not None:
            return record

        record = SnapshotCacheRecord(cache_status="empty")
        db.add(record)
        db.flush()
        return record

    def mark_refreshing(self, db: Session) -> SnapshotCacheRecord:
        record = self.get_or_create(db)
        record.cache_status = "refreshing"
        record.refresh_started_at = datetime.now(timezone.utc)
        return record

    def save_success(self, db: Session, snapshot: CanonicalSnapshot) -> SnapshotCacheRecord:
        record = self.get_or_create(db)
        record.snapshot_json = snapshot.model_dump_json()
        record.cache_status = "success"
        record.last_success_at = datetime.now(timezone.utc)
        record.last_error = ""
        return record

    def save_failure(self, db: Session, error: str) -> SnapshotCacheRecord:
        record = self.get_or_create(db)
        record.cache_status = "failed"
        record.last_error_at = datetime.now(timezone.utc)
        record.last_error = error
        return record
