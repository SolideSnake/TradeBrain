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
