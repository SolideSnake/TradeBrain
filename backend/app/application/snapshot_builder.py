from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.adapters.ibkr.client import IBKRClient, get_ibkr_client
from app.adapters.persistence.sqlite.watchlist_repository import WatchlistRepository
from app.domains.snapshot.schemas import (
    CanonicalSnapshot,
    CanonicalWatchlistItem,
    SnapshotMeta,
    SnapshotSummary,
)


class SnapshotBuilder:
    def __init__(
        self,
        watchlist_repository: WatchlistRepository | None = None,
        ibkr_client: IBKRClient | None = None,
    ) -> None:
        self.watchlist_repository = watchlist_repository or WatchlistRepository()
        self.ibkr_client = ibkr_client or get_ibkr_client()

    def build(self, db: Session) -> CanonicalSnapshot:
        watchlist_entries = self.watchlist_repository.list(db)
        broker_snapshot = self.ibkr_client.fetch_snapshot(
            [entry.symbol for entry in watchlist_entries if entry.enabled]
        )
        positions_by_symbol = {position.symbol: position for position in broker_snapshot.positions}

        watchlist = [
            CanonicalWatchlistItem(
                id=entry.id,
                symbol=entry.symbol,
                name=entry.name,
                market=entry.market,
                asset_type=entry.asset_type,
                group_name=entry.group_name,
                enabled=entry.enabled,
                in_position=entry.in_position,
                notes=entry.notes,
                quote=broker_snapshot.quotes.get(entry.symbol),
                position=positions_by_symbol.get(entry.symbol),
            )
            for entry in watchlist_entries
        ]

        summary = SnapshotSummary(
            tracked_symbols=len(watchlist),
            enabled_symbols=sum(1 for entry in watchlist if entry.enabled),
            symbols_in_position=sum(1 for entry in watchlist if entry.in_position),
            quote_coverage=sum(1 for entry in watchlist if entry.quote is not None),
            position_count=len(broker_snapshot.positions),
        )

        return CanonicalSnapshot(
            meta=SnapshotMeta(
                generated_at=datetime.now(UTC),
                broker_mode=broker_snapshot.mode,
                broker_status=broker_snapshot.status,
                warnings=broker_snapshot.warnings,
            ),
            summary=summary,
            account=broker_snapshot.account,
            watchlist=watchlist,
            positions=broker_snapshot.positions,
        )
