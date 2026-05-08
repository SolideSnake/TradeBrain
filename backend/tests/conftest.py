from __future__ import annotations

from pathlib import Path
from datetime import UTC, datetime
from typing import Sequence

import pytest
from fastapi.testclient import TestClient

from app.adapters.ibkr.client import IBKRClient, get_ibkr_client
from app.adapters.telegram.client import get_telegram_notifier
from app.adapters.persistence.sqlite.db import get_engine, get_session_factory
from app.application.snapshot_builder import SnapshotBuilder
from app.config.settings import get_settings
from app.domains.fundamentals.schemas import FundamentalSnapshot
from app.domains.indicators.schemas import PriceReferenceLevels
from app.domains.market.schemas import QuoteSnapshot
from app.domains.portfolio.schemas import AccountSnapshot
from app.domains.snapshot.schemas import BrokerSnapshotEnvelope
from app.main import create_app


class TestIBKRClient(IBKRClient):
    def fetch_snapshot(self, tracked_symbols: Sequence[str]) -> BrokerSnapshotEnvelope:
        now = datetime.now(UTC)
        unique_symbols = sorted({symbol.strip().upper() for symbol in tracked_symbols if symbol})
        quotes = {symbol: self._build_quote(symbol, now) for symbol in unique_symbols}
        reference_levels = {
            symbol: self._build_reference_levels(symbol, now) for symbol in unique_symbols
        }
        fundamentals = {
            symbol: self._build_fundamentals(symbol, now) for symbol in unique_symbols
        }

        return BrokerSnapshotEnvelope(
            mode="live",
            status="connected",
            profile="paper",
            display_name="测试 TWS Paper",
            account=AccountSnapshot(
                account_id="TEST-ACCOUNT",
                net_liquidation=250000.0,
                cash_balance=82000.0,
                settled_cash=82000.0,
                available_funds=82000.0,
                buying_power=164000.0,
                currency="USD",
                source="test",
                updated_at=now,
            ),
            positions=[],
            quotes=quotes,
            reference_levels=reference_levels,
            fundamentals=fundamentals,
        )

    def _build_quote(self, symbol: str, now: datetime) -> QuoteSnapshot:
        seed = sum(ord(character) for character in symbol)
        previous_close = round(20 + (seed % 240) + ((seed % 17) / 10), 2)
        drift = ((seed % 9) - 4) / 100
        last_price = round(previous_close * (1 + drift), 2)
        change_percent = round(((last_price - previous_close) / previous_close) * 100, 2)
        return QuoteSnapshot(
            symbol=symbol,
            last_price=last_price,
            previous_close=previous_close,
            change_percent=change_percent,
            bid=round(last_price - 0.05, 2),
            ask=round(last_price + 0.05, 2),
            currency="USD",
            as_of=now,
            source="test",
        )

    def _build_reference_levels(self, symbol: str, now: datetime) -> PriceReferenceLevels:
        quote = self._build_quote(symbol, now)
        last_price = quote.last_price or 0.0
        return PriceReferenceLevels(
            high_52w=round(last_price * 1.18, 2) if last_price else None,
            low_52w=round(last_price * 0.72, 2) if last_price else None,
            high_90d=round(last_price * 1.08, 2) if last_price else None,
            low_90d=round(last_price * 0.88, 2) if last_price else None,
            source="test",
            as_of=now,
        )

    def _build_fundamentals(self, symbol: str, now: datetime) -> FundamentalSnapshot:
        seed = sum(ord(character) for character in symbol)
        pe_ratio = round(10 + (seed % 18) + ((seed % 10) / 10), 2)
        growth = round(8 + (seed % 28) + ((seed % 9) / 10), 2)
        peg_ratio = round(pe_ratio / growth, 2) if growth > 0 else None
        return FundamentalSnapshot(
            pe_ratio=pe_ratio,
            earnings_growth_rate_percent=growth,
            peg_ratio=peg_ratio,
            source="test",
            as_of=now,
        )


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "")
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
    get_ibkr_client.cache_clear()
    get_telegram_notifier.cache_clear()

    app = create_app()
    from app.api import router as router_module

    previous_builder = router_module.snapshot_cache_service.snapshot_builder
    router_module.snapshot_cache_service.snapshot_builder = SnapshotBuilder(
        ibkr_client=TestIBKRClient()
    )
    with TestClient(app) as test_client:
        yield test_client

    router_module.snapshot_cache_service.snapshot_builder = previous_builder

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
    get_ibkr_client.cache_clear()
    get_telegram_notifier.cache_clear()
