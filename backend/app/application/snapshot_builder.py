from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.adapters.ibkr.client import IBKRClient, LiveIBKRClient, MockIBKRClient
from app.adapters.persistence.sqlite.watchlist_repository import WatchlistRepository
from app.application.alert_router import AlertRouter
from app.application.ibkr_settings_service import IBKRSettingsService
from app.application.state_engine import StateEngine
from app.config.settings import Settings, get_settings
from app.domains.indicators.service import IndicatorService
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
        indicator_service: IndicatorService | None = None,
        state_engine: StateEngine | None = None,
        alert_router: AlertRouter | None = None,
        ibkr_settings_service: IBKRSettingsService | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.watchlist_repository = watchlist_repository or WatchlistRepository()
        self.ibkr_client = ibkr_client
        self.indicator_service = indicator_service or IndicatorService()
        self.state_engine = state_engine or StateEngine()
        self.alert_router = alert_router or AlertRouter()
        self.ibkr_settings_service = ibkr_settings_service or IBKRSettingsService()
        self.settings = settings or get_settings()

    def build(self, db: Session) -> CanonicalSnapshot:
        watchlist_entries = self.watchlist_repository.list(db)
        ibkr_client = self._resolve_ibkr_client(db)
        broker_snapshot = ibkr_client.fetch_snapshot(
            [entry.symbol for entry in watchlist_entries if entry.enabled]
        )
        positions_by_symbol = {
            position.symbol: self.indicator_service.enrich_position(
                position,
                broker_snapshot.quotes.get(position.symbol),
            )
            for position in broker_snapshot.positions
        }

        indicators_by_symbol = {}
        for entry in watchlist_entries:
            indicators_by_symbol[entry.symbol] = self.indicator_service.build(
                broker_snapshot.quotes.get(entry.symbol),
                positions_by_symbol.get(entry.symbol),
                broker_snapshot.reference_levels.get(entry.symbol),
                broker_snapshot.fundamentals.get(entry.symbol),
            )

        states_by_symbol = self.state_engine.evaluate_symbols(db, indicators_by_symbol)
        self.alert_router.route_state_changes(db, states_by_symbol, indicators_by_symbol)

        watchlist: list[CanonicalWatchlistItem] = []
        for entry in watchlist_entries:
            quote = broker_snapshot.quotes.get(entry.symbol)
            position = positions_by_symbol.get(entry.symbol)
            reference_levels = broker_snapshot.reference_levels.get(entry.symbol)
            fundamentals = broker_snapshot.fundamentals.get(entry.symbol)
            indicators = indicators_by_symbol.get(entry.symbol)

            watchlist.append(
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
                    quote=quote,
                    position=position,
                    reference_levels=reference_levels,
                    fundamentals=fundamentals,
                    indicators=indicators,
                    state=states_by_symbol.get(entry.symbol),
                )
            )

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
                broker_profile=broker_snapshot.profile,
                broker_display_name=broker_snapshot.display_name,
                warnings=broker_snapshot.warnings,
            ),
            summary=summary,
            account=broker_snapshot.account,
            watchlist=watchlist,
            positions=list(positions_by_symbol.values()),
        )

    def _resolve_ibkr_client(self, db: Session) -> IBKRClient:
        if self.ibkr_client is not None:
            return self.ibkr_client

        mode, profile = self.ibkr_settings_service.resolve_runtime_profile(db)
        if mode == "ibkr":
            return LiveIBKRClient(self.settings, profile)
        return MockIBKRClient(self.settings)
