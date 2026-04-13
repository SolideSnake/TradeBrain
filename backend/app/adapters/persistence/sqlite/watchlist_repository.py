from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domains.watchlist.errors import DuplicateWatchlistSymbolError
from app.domains.watchlist.models import WatchlistEntry
from app.domains.watchlist.schemas import WatchlistEntryCreate, WatchlistEntryUpdate


class WatchlistRepository:
    def list(self, db: Session) -> list[WatchlistEntry]:
        query = select(WatchlistEntry).order_by(WatchlistEntry.symbol.asc())
        return list(db.scalars(query))

    def get(self, db: Session, entry_id: int) -> WatchlistEntry | None:
        return db.get(WatchlistEntry, entry_id)

    def create(self, db: Session, payload: WatchlistEntryCreate) -> WatchlistEntry:
        entry = WatchlistEntry(**payload.model_dump())
        db.add(entry)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise DuplicateWatchlistSymbolError(payload.symbol) from exc
        db.refresh(entry)
        return entry

    def update(
        self, db: Session, entry: WatchlistEntry, payload: WatchlistEntryUpdate
    ) -> WatchlistEntry:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(entry, field, value)
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    def delete(self, db: Session, entry: WatchlistEntry) -> None:
        db.delete(entry)
        db.commit()
