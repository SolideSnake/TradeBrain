from __future__ import annotations

from sqlalchemy.orm import Session

from app.application.notifications import NotificationService
from app.application.snapshot_builder import SnapshotBuilder
from app.application.state_engine import StateEngine
from app.domains.snapshot.schemas import CanonicalSnapshot


class SnapshotPipelineService:
    def __init__(
        self,
        snapshot_builder: SnapshotBuilder | None = None,
        state_engine: StateEngine | None = None,
        notification_service: NotificationService | None = None,
    ) -> None:
        self.snapshot_builder = snapshot_builder or SnapshotBuilder()
        self.state_engine = state_engine or StateEngine()
        self.notification_service = notification_service or NotificationService()

    def build_snapshot(self, db: Session) -> CanonicalSnapshot:
        snapshot = self.snapshot_builder.build(db)
        snapshot_with_states = self._attach_states(db, snapshot)
        self.notification_service.handle_snapshot(db, snapshot_with_states)
        return snapshot_with_states

    def _attach_states(self, db: Session, snapshot: CanonicalSnapshot) -> CanonicalSnapshot:
        indicators_by_symbol = {
            item.symbol: item.indicators
            for item in snapshot.watchlist
        }
        states_by_symbol = self.state_engine.evaluate_symbols(db, indicators_by_symbol)
        watchlist = [
            item.model_copy(update={"state": states_by_symbol.get(item.symbol)})
            for item in snapshot.watchlist
        ]
        return snapshot.model_copy(update={"watchlist": watchlist})
