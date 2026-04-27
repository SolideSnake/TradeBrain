from datetime import datetime, timezone
from types import SimpleNamespace

from app.adapters.ibkr.client import LiveIBKRClient
from app.config.settings import Settings


def test_live_ibkr_client_ignores_zero_last_price_and_uses_close():
    client = LiveIBKRClient(Settings())
    ticker = SimpleNamespace(last=0.0, close=273.05, bid=-1, ask=-1)

    assert client._resolve_last_price(ticker) == 273.05


def test_live_ibkr_client_ignores_invalid_bid_ask_prices():
    client = LiveIBKRClient(Settings())

    assert client._to_positive_price(-1) is None
    assert client._to_positive_price(0) is None
    assert client._to_positive_price(201.7) == 201.7


def test_live_ibkr_client_uses_safe_minimum_timeouts():
    client = LiveIBKRClient(
        Settings(
            ibkr_connect_timeout_seconds=0.1,
            ibkr_request_timeout_seconds=0.1,
        )
    )

    assert client._connect_timeout_seconds() == 1.0
    assert client._request_timeout_seconds() == 1.0


def test_live_ibkr_client_uses_configured_timeouts():
    client = LiveIBKRClient(
        Settings(
            ibkr_connect_timeout_seconds=6.5,
            ibkr_request_timeout_seconds=15.0,
        )
    )

    assert client._connect_timeout_seconds() == 6.5
    assert client._request_timeout_seconds() == 15.0


def test_live_ibkr_client_builds_high_and_low_reference_levels():
    client = LiveIBKRClient(Settings())
    bars = [
        SimpleNamespace(high=100.0, low=80.0, date="20260102"),
        SimpleNamespace(high=110.0, low=90.0, date="20260320"),
        SimpleNamespace(high=105.0, low=85.0, date="20260420"),
    ]

    levels = client._reference_levels_from_bars(
        bars,
        now=datetime(2026, 4, 27, tzinfo=timezone.utc),
    )

    assert levels.high_52w == 110.0
    assert levels.low_52w == 80.0
    assert levels.high_90d == 110.0
    assert levels.low_90d == 85.0
