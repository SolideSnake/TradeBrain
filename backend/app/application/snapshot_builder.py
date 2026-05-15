from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.adapters.ibkr.client import IBKRClient, LiveIBKRClient
from app.adapters.persistence.sqlite.fx_rate_repository import FxRateRepository
from app.adapters.persistence.sqlite.watchlist_repository import WatchlistRepository
from app.application.ibkr_settings_service import IBKRSettingsService
from app.config.settings import Settings, get_settings
from app.domains.fx import FxConversionService
from app.domains.fx.schemas import FxRateSnapshot
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
        fx_conversion_service: FxConversionService | None = None,
        fx_rate_repository: FxRateRepository | None = None,
        ibkr_settings_service: IBKRSettingsService | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.watchlist_repository = watchlist_repository or WatchlistRepository()
        self.ibkr_client = ibkr_client
        self.indicator_service = indicator_service or IndicatorService()
        self.fx_conversion_service = fx_conversion_service or FxConversionService()
        self.fx_rate_repository = fx_rate_repository or FxRateRepository()
        self.ibkr_settings_service = ibkr_settings_service or IBKRSettingsService()
        self.settings = settings or get_settings()

    def build(self, db: Session) -> CanonicalSnapshot:
        watchlist_entries = self.watchlist_repository.list(db)
        ibkr_client = self._resolve_ibkr_client(db)
        broker_snapshot = ibkr_client.fetch_snapshot(
            [entry.symbol for entry in watchlist_entries if entry.enabled]
        )
        fx_rates = self._resolve_fx_rates(
            db,
            broker_snapshot.fx_rates,
            {
                *{position.currency for position in broker_snapshot.positions},
                *{quote.currency for quote in broker_snapshot.quotes.values()},
            },
            broker_snapshot.account.currency,
            broker_snapshot.warnings,
        )
        quotes_by_symbol = {
            symbol: self.fx_conversion_service.convert_quote(
                quote,
                broker_snapshot.account.currency,
                fx_rates,
            )
            for symbol, quote in broker_snapshot.quotes.items()
        }
        positions_by_symbol = {
            position.symbol: self.fx_conversion_service.convert_position(
                self.indicator_service.enrich_position(
                    position,
                    quotes_by_symbol.get(position.symbol),
                ),
                broker_snapshot.account.currency,
                fx_rates,
            )
            for position in broker_snapshot.positions
        }

        indicators_by_symbol = {}
        for entry in watchlist_entries:
            indicators_by_symbol[entry.symbol] = self.indicator_service.build(
                quotes_by_symbol.get(entry.symbol),
                positions_by_symbol.get(entry.symbol),
                broker_snapshot.reference_levels.get(entry.symbol),
                broker_snapshot.fundamentals.get(entry.symbol),
            )

        watchlist: list[CanonicalWatchlistItem] = []
        for entry in watchlist_entries:
            quote = quotes_by_symbol.get(entry.symbol)
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
                )
            )

        summary = SnapshotSummary(
            tracked_symbols=len(watchlist),
            enabled_symbols=sum(1 for entry in watchlist if entry.enabled),
            symbols_in_position=sum(1 for entry in watchlist if entry.in_position),
            quote_coverage=sum(1 for entry in watchlist if entry.quote is not None),
            position_count=len(broker_snapshot.positions),
        )

        snapshot = CanonicalSnapshot(
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
        return snapshot

    def _resolve_fx_rates(
        self,
        db: Session,
        fresh_rates: dict[str, FxRateSnapshot],
        currencies: set[str],
        base_currency: str,
        warnings: list[str],
    ) -> dict[str, FxRateSnapshot]:
        normalized_base = base_currency.strip().upper() or "USD"
        rates: dict[str, FxRateSnapshot] = {}

        for rate in fresh_rates.values():
            if rate.to_currency != normalized_base:
                continue
            rates[rate.from_currency] = rate
            if rate.source != "identity":
                self.fx_rate_repository.upsert(db, rate)

        db.commit()

        for currency in sorted({currency.strip().upper() for currency in currencies if currency}):
            if currency == normalized_base:
                rates[currency] = FxRateSnapshot(
                    from_currency=currency,
                    to_currency=normalized_base,
                    rate=1.0,
                    source="identity",
                    as_of=datetime.now(UTC),
                )
                continue
            if currency in rates:
                continue

            cached_rate = self.fx_rate_repository.get_recent(
                db,
                currency,
                normalized_base,
                max_age=timedelta(hours=1),
            )
            if cached_rate is not None:
                rates[currency] = cached_rate
                warnings.append(f"Using cached FX rate for {currency}->{normalized_base}.")

        return rates

    def _resolve_ibkr_client(self, db: Session) -> IBKRClient:
        if self.ibkr_client is not None:
            return self.ibkr_client

        _mode, profile = self.ibkr_settings_service.resolve_runtime_profile(db)
        return LiveIBKRClient(self.settings, profile)
