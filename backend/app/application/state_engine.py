from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.adapters.persistence.sqlite.state_repository import StateRepository
from app.domains.indicators.schemas import IndicatorSnapshot
from app.domains.state.schemas import WatchlistStateSnapshot
from app.domains.state.service import StateService


class StateEngine:
    def __init__(
        self,
        state_repository: StateRepository | None = None,
        state_service: StateService | None = None,
    ) -> None:
        self.state_repository = state_repository or StateRepository()
        self.state_service = state_service or StateService()

    def evaluate_symbols(
        self,
        db: Session,
        indicators_by_symbol: dict[str, IndicatorSnapshot | None],
    ) -> dict[str, WatchlistStateSnapshot]:
        evaluated_at = datetime.now(UTC)
        existing_states = self.state_repository.list_by_symbols(db, list(indicators_by_symbol.keys()))
        next_states: dict[str, WatchlistStateSnapshot] = {}

        for symbol, indicators in indicators_by_symbol.items():
            label = indicators.valuation_label if indicators else None
            state, update_payload = self.state_service.evaluate(
                symbol=symbol,
                current_label=label,
                existing_state=existing_states.get(symbol),
                evaluated_at=evaluated_at,
            )
            self.state_repository.upsert(db, symbol, update_payload)
            next_states[symbol] = state

        if indicators_by_symbol:
            db.commit()

        return next_states

    def list_states(self, db: Session) -> list[WatchlistStateSnapshot]:
        return [
            WatchlistStateSnapshot.model_validate(state, from_attributes=True)
            for state in self.state_repository.list(db)
        ]
