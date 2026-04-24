from __future__ import annotations

from sqlalchemy.orm import Session

from app.adapters.persistence.sqlite.snapshot_repository import SnapshotRepository
from app.application.snapshot_pipeline_service import SnapshotPipelineService
from app.domains.scanner import ScannerResult, ScannerService
from app.domains.snapshot.schemas import CanonicalSnapshot


class ScannerApplicationService:
    def __init__(
        self,
        snapshot_repository: SnapshotRepository | None = None,
        snapshot_pipeline_service: SnapshotPipelineService | None = None,
        scanner_service: ScannerService | None = None,
    ) -> None:
        self.snapshot_repository = snapshot_repository or SnapshotRepository()
        self.snapshot_pipeline_service = snapshot_pipeline_service or SnapshotPipelineService()
        self.scanner_service = scanner_service or ScannerService()

    def scan_latest(self, db: Session) -> ScannerResult:
        snapshot = self._latest_snapshot(db)
        return self.scanner_service.scan_snapshot(snapshot)

    def _latest_snapshot(self, db: Session) -> CanonicalSnapshot:
        record = self.snapshot_repository.get(db)
        if record and record.snapshot_json:
            return CanonicalSnapshot.model_validate_json(record.snapshot_json)
        return self.snapshot_pipeline_service.build_snapshot(db)
