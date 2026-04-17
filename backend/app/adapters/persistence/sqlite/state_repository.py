from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.state.models import WatchlistState


class StateRepository:
    def list(self, db: Session) -> list[WatchlistState]:
        query = select(WatchlistState).order_by(WatchlistState.symbol.asc())
        return list(db.scalars(query))

    def list_by_symbols(self, db: Session, symbols: list[str]) -> dict[str, WatchlistState]:
        if not symbols:
            return {}

        query = select(WatchlistState).where(WatchlistState.symbol.in_(symbols))
        rows = list(db.scalars(query))
        return {row.symbol: row for row in rows}

    def upsert(self, db: Session, symbol: str, payload: dict[str, object]) -> WatchlistState:
        state = db.scalar(select(WatchlistState).where(WatchlistState.symbol == symbol))
        if state is None:
            state = WatchlistState(symbol=symbol, **payload)
            db.add(state)
        else:
            for field, value in payload.items():
                setattr(state, field, value)
            db.add(state)
        return state
