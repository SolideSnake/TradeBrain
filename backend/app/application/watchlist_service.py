from __future__ import annotations

from sqlalchemy.orm import Session

from app.adapters.persistence.sqlite.watchlist_repository import WatchlistRepository
from app.domains.watchlist.models import WatchlistEntry
from app.domains.watchlist.schemas import WatchlistEntryCreate, WatchlistEntryUpdate


class WatchlistService:
    def __init__(self, repository: WatchlistRepository | None = None) -> None:
        self.repository = repository or WatchlistRepository()

    def list_entries(self, db: Session) -> list[WatchlistEntry]:
        return self.repository.list(db)

    def create_entry(self, db: Session, payload: WatchlistEntryCreate) -> WatchlistEntry:
        return self.repository.create(db, payload)

    def update_entry(
        self, db: Session, entry_id: int, payload: WatchlistEntryUpdate
    ) -> WatchlistEntry | None:
        entry = self.repository.get(db, entry_id)
        if entry is None:
            return None
        return self.repository.update(db, entry, payload)

    def delete_entry(self, db: Session, entry_id: int) -> bool:
        entry = self.repository.get(db, entry_id)
        if entry is None:
            return False
        self.repository.delete(db, entry)
        return True

