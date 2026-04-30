from datetime import datetime, timezone
from types import SimpleNamespace

from app.adapters.ibkr.client import LiveIBKRClient
from app.config.settings import Settings


def test_live_ibkr_client_ignores_zero_last_price_and_uses_close():
    client = LiveIBKRClient(Settings())
    ticker = SimpleNamespace(last=0.0, close=273.05, bid=-1, ask=-1)

    assert client._resolve_last_price(ticker) == 273.05


def test_live_ibkr_client_uses_previous_close_as_price_fallback():
    client = LiveIBKRClient(Settings())
    ticker = SimpleNamespace(last=0.0, close=-1, previousClose=142000.0, bid=-1, ask=-1)

    assert client._resolve_last_price(ticker) == 142000.0
    assert client._resolve_previous_close(ticker) == 142000.0


def test_live_ibkr_client_uses_market_price_before_close():
    client = LiveIBKRClient(Settings())
    ticker = SimpleNamespace(
        last=0.0,
        close=273.05,
        previousClose=270.0,
        bid=-1,
        ask=-1,
        marketPrice=lambda: 275.5,
    )

    assert client._resolve_last_price(ticker) == 275.5


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


def test_live_ibkr_client_skips_invalid_qualified_contracts():
    client = LiveIBKRClient(Settings())
    warnings: list[str] = []

    class FakeIB:
        def qualifyContracts(self, contract):
            return [None]

    class FakeStock:
        def __init__(self, symbol, exchange, currency):
            self.symbol = symbol
            self.exchange = exchange
            self.currency = currency

    contracts = client._build_stock_contracts(
        FakeIB(),
        FakeStock,
        ["MDC"],
        warnings,
    )

    assert contracts == {}
    assert warnings == ["Failed to qualify stock contract for MDC."]


def test_live_ibkr_client_converts_dot_symbol_for_ibkr_class_shares():
    client = LiveIBKRClient(Settings())

    assert client._to_ibkr_stock_symbol("BRK.B") == "BRK B"


def test_live_ibkr_client_uses_korean_contract_for_six_digit_symbol():
    client = LiveIBKRClient(Settings())

    assert client._stock_contract_spec("000660") == ("000660", "KRX", "KRW")
    assert client._quote_currency("000660", SimpleNamespace(currency="USD")) == "KRW"


def test_live_ibkr_client_builds_korean_stock_contract():
    client = LiveIBKRClient(Settings())
    warnings: list[str] = []
    created_contracts = []

    class FakeIB:
        def qualifyContracts(self, contract):
            contract.secType = "STK"
            return [contract]

    class FakeStock:
        def __init__(self, symbol, exchange, currency):
            self.symbol = symbol
            self.exchange = exchange
            self.currency = currency
            created_contracts.append(self)

    contracts = client._build_stock_contracts(
        FakeIB(),
        FakeStock,
        ["000660"],
        warnings,
    )

    assert list(contracts) == ["000660"]
    assert created_contracts[0].symbol == "000660"
    assert created_contracts[0].exchange == "KRX"
    assert created_contracts[0].currency == "KRW"
    assert warnings == []


def test_live_ibkr_client_separates_cash_from_available_funds():
    client = LiveIBKRClient(Settings())

    class FakeIB:
        def accountSummary(self, account_id):
            return [
                SimpleNamespace(tag="NetLiquidation", currency="USD", value="73372.47"),
                SimpleNamespace(tag="TotalCashValue", currency="USD", value="-5277.89"),
                SimpleNamespace(tag="AvailableFunds", currency="USD", value="53376.56"),
                SimpleNamespace(tag="BuyingPower", currency="USD", value="213506.24"),
            ]

    account = client._build_account_snapshot(
        FakeIB(),
        "U123",
        datetime(2026, 4, 30, tzinfo=timezone.utc),
    )

    assert account.cash_balance == -5277.89
    assert account.available_funds == 53376.56
    assert account.buying_power == 213506.24


def test_live_ibkr_client_builds_fx_rates_for_non_base_currency():
    class FakeClient(LiveIBKRClient):
        def _fetch_fx_rate_to_base(self, ib, forex_cls, from_currency, base_currency):
            if (from_currency, base_currency) == ("KRW", "USD"):
                return 0.00072
            return None

    client = FakeClient(Settings())
    warnings: list[str] = []

    rates = client._build_fx_rates(
        ib=None,
        forex_cls=None,
        currencies={"USD", "KRW"},
        base_currency="USD",
        now=datetime(2026, 4, 30, tzinfo=timezone.utc),
        warnings=warnings,
    )

    assert rates["USD"].rate == 1.0
    assert rates["KRW"].rate == 0.00072
    assert rates["KRW"].to_currency == "USD"
    assert warnings == []
