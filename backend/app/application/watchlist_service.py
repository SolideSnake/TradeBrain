from __future__ import annotations

from sqlalchemy.orm import Session

from app.adapters.persistence.sqlite.watchlist_repository import WatchlistRepository
from app.core.types.common import Market
from app.domains.watchlist.models import WatchlistEntry
from app.domains.watchlist.schemas import WatchlistEntryCreate, WatchlistEntryUpdate


SYMBOL_NAME_OVERRIDES = {
    "AAPL": "Apple Inc.",
    "AMZN": "Amazon.com, Inc.",
    "GOOG": "Alphabet Inc.",
    "GOOGL": "Alphabet Inc.",
    "MCD": "McDonald's Corporation",
    "META": "Meta Platforms, Inc.",
    "MSFT": "Microsoft Corporation",
    "NVDA": "NVIDIA Corporation",
    "QQQ": "Invesco QQQ Trust",
    "RSP": "Invesco S&P 500 Equal Weight ETF",
    "SGOV": "iShares 0-3 Month Treasury Bond ETF",
    "SPY": "SPDR S&P 500 ETF Trust",
    "TLT": "iShares 20+ Year Treasury Bond ETF",
    "TSLA": "Tesla, Inc.",
    "VOO": "Vanguard S&P 500 ETF",
    "000660": "SK hynix Inc.",
}


class WatchlistService:
    def __init__(self, repository: WatchlistRepository | None = None) -> None:
        self.repository = repository or WatchlistRepository()

    def list_entries(self, db: Session) -> list[WatchlistEntry]:
        return self.repository.list(db)

    def create_entry(self, db: Session, payload: WatchlistEntryCreate) -> WatchlistEntry:
        if "market" not in payload.model_fields_set:
            payload.market = self._infer_market(payload.symbol)
        payload.name = self._resolve_display_name(payload.symbol, payload.name)
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

    def _resolve_display_name(self, symbol: str, submitted_name: str | None) -> str:
        if submitted_name:
            return submitted_name
        return SYMBOL_NAME_OVERRIDES.get(symbol, symbol)

    def _infer_market(self, symbol: str) -> Market:
        if symbol.isdigit() and len(symbol) == 6:
            return Market.KR
        return Market.US

