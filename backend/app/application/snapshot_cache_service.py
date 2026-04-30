from __future__ import annotations

from threading import Lock

from sqlalchemy.orm import Session

from app.adapters.persistence.sqlite.snapshot_repository import SnapshotRepository
from app.application.event_service import EventService
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
        event_service: EventService | None = None,
    ) -> None:
        self.repository = repository or SnapshotRepository()
        self.snapshot_pipeline_service = snapshot_pipeline_service
        self.snapshot_builder = snapshot_builder
        self.event_service = event_service or EventService()

    def get_latest(self, db: Session) -> SnapshotResponse:
        record = self.repository.get(db)
        if record and record.snapshot_json:
            return self._build_response(record, from_cache=True)
        return self.refresh(db, trigger="initial")

    def refresh(self, db: Session, trigger: str = "manual") -> SnapshotResponse:
        if not _REFRESH_LOCK.acquire(blocking=False):
            return self._build_refreshing_response(db, trigger=trigger)

        try:
            self.repository.mark_refreshing(db)
            db.commit()

            try:
                snapshot = self._snapshot_pipeline.build_snapshot(db)
            except Exception as exc:
                record = self.repository.save_failure(db, str(exc))
                self._record_refresh_event(
                    db,
                    trigger=trigger,
                    status="failed",
                    severity="warning",
                    title="快照刷新失败",
                    message=str(exc),
                )
                db.commit()
                db.refresh(record)
                return self._build_response(record, from_cache=bool(record.snapshot_json))

            record = self.repository.save_success(db, snapshot)
            self._record_refresh_event(
                db,
                trigger=trigger,
                status="success",
                severity="info",
                title="快照刷新成功",
                message=self._build_success_message(snapshot),
                payload={
                    "broker_status": snapshot.meta.broker_status,
                    "broker_profile": snapshot.meta.broker_profile,
                    "broker_display_name": snapshot.meta.broker_display_name,
                    "tracked_symbols": snapshot.summary.tracked_symbols,
                    "quote_coverage": snapshot.summary.quote_coverage,
                },
            )
            db.commit()
            db.refresh(record)
            return self._build_response(record, from_cache=False)
        finally:
            _REFRESH_LOCK.release()

    def _build_refreshing_response(self, db: Session, trigger: str) -> SnapshotResponse:
        record = self.repository.mark_refreshing(db)
        self._record_refresh_event(
            db,
            trigger=trigger,
            status="skipped",
            severity="info",
            title="快照刷新跳过",
            message="已有一轮快照刷新正在执行，本次请求已跳过。",
        )
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

    def _record_refresh_event(
        self,
        db: Session,
        *,
        trigger: str,
        status: str,
        severity: str,
        title: str,
        message: str,
        payload: dict | None = None,
    ) -> None:
        event_payload = {"trigger": trigger, **(payload or {})}
        self.event_service.record_event(
            db,
            event_type="snapshot.refresh",
            source="snapshot",
            severity=severity,
            title=title,
            message=message,
            status=status,
            entity_type="snapshot",
            payload=event_payload,
        )

    def _build_success_message(self, snapshot: CanonicalSnapshot) -> str:
        return (
            f"{snapshot.meta.broker_display_name} 刷新完成，"
            f"行情覆盖 {snapshot.summary.quote_coverage}/"
            f"{snapshot.summary.tracked_symbols}。"
        )

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
