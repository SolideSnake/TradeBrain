from __future__ import annotations

from datetime import UTC, datetime

from app.core.types.common import ValuationLabel
from app.domains.state.models import WatchlistState
from app.domains.state.schemas import WatchlistStateSnapshot


class StateService:
    def evaluate(
        self,
        symbol: str,
        current_label: ValuationLabel | None,
        existing_state: WatchlistState | None,
        evaluated_at: datetime | None = None,
    ) -> tuple[WatchlistStateSnapshot, dict[str, object]]:
        evaluated_at = evaluated_at or datetime.now(UTC)
        previous_label = existing_state.current_label if existing_state else None
        has_changed = existing_state is not None and previous_label != current_label
        changed_at = evaluated_at if has_changed else (existing_state.changed_at if existing_state else None)

        state = WatchlistStateSnapshot(
            symbol=symbol,
            current_label=current_label,
            previous_label=previous_label,
            has_changed=has_changed,
            changed_at=changed_at,
            evaluated_at=evaluated_at,
        )
        update_payload: dict[str, object] = {
            "current_label": current_label,
            "previous_label": previous_label,
            "changed_at": changed_at,
            "evaluated_at": evaluated_at,
        }
        return state, update_payload
