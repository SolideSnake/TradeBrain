from datetime import UTC, datetime

from app.domains.fx.schemas import FxRateSnapshot
from app.domains.fx.service import FxConversionService
from app.domains.market.schemas import QuoteSnapshot
from app.domains.portfolio.schemas import PositionSnapshot


def test_fx_conversion_service_adds_base_currency_values():
    position = PositionSnapshot(
        symbol="000660",
        quantity=6,
        average_cost=1_250_000,
        market_price=1_293_000,
        market_value=7_758_000,
        unrealized_pnl=258_000,
        currency="KRW",
        account_id="U123",
    )
    rates = {
        "KRW": FxRateSnapshot(
            from_currency="KRW",
            to_currency="USD",
            rate=0.00072,
            source="test",
            as_of=datetime.now(UTC),
        )
    }

    converted = FxConversionService().convert_position(position, "USD", rates)

    assert converted.currency == "KRW"
    assert converted.base_currency == "USD"
    assert converted.fx_rate_to_base == 0.00072
    assert converted.market_value == 7_758_000
    assert converted.market_value_base == 5585.76
    assert converted.unrealized_pnl_base == 185.76


def test_fx_conversion_service_leaves_base_values_empty_without_rate():
    position = PositionSnapshot(
        symbol="000660",
        quantity=6,
        market_value=7_758_000,
        currency="KRW",
        account_id="U123",
    )

    converted = FxConversionService().convert_position(position, "USD", {})

    assert converted.market_value == 7_758_000
    assert converted.market_value_base is None
    assert converted.fx_rate_to_base is None


def test_fx_conversion_service_adds_base_currency_quote_values():
    quote = QuoteSnapshot(
        symbol="000660",
        last_price=1_976_000,
        previous_close=1_835_000,
        bid=1_975_000,
        ask=1_977_000,
        currency="KRW",
        source="test",
    )
    rates = {
        "KRW": FxRateSnapshot(
            from_currency="KRW",
            to_currency="USD",
            rate=0.00072,
            source="test",
            as_of=datetime.now(UTC),
        )
    }

    converted = FxConversionService().convert_quote(quote, "USD", rates)

    assert converted.currency == "KRW"
    assert converted.base_currency == "USD"
    assert converted.fx_rate_to_base == 0.00072
    assert converted.last_price == 1_976_000
    assert converted.last_price_base == 1422.72
    assert converted.previous_close_base == 1321.2


def test_fx_conversion_service_leaves_quote_base_values_empty_without_rate():
    quote = QuoteSnapshot(
        symbol="000660",
        last_price=1_976_000,
        currency="KRW",
        source="test",
    )

    converted = FxConversionService().convert_quote(quote, "USD", {})

    assert converted.currency == "KRW"
    assert converted.base_currency == "USD"
    assert converted.last_price == 1_976_000
    assert converted.last_price_base is None
    assert converted.fx_rate_to_base is None
