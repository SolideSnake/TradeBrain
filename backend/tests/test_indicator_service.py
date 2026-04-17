from app.core.types.common import ValuationLabel
from app.domains.fundamentals.schemas import FundamentalSnapshot
from app.domains.indicators.schemas import PriceReferenceLevels
from app.domains.indicators.service import IndicatorService
from app.domains.market.schemas import QuoteSnapshot
from app.domains.portfolio.schemas import PositionSnapshot


def test_indicator_service_builds_watchlist_metrics():
    service = IndicatorService()
    quote = QuoteSnapshot(
        symbol="AAPL",
        last_price=180.0,
        previous_close=175.0,
        change_percent=2.86,
        source="test",
    )
    position = PositionSnapshot(
        symbol="AAPL",
        quantity=10,
        average_cost=150.0,
        currency="USD",
    )
    reference_levels = PriceReferenceLevels(
        high_52w=200.0,
        high_90d=190.0,
        source="test",
    )
    fundamentals = FundamentalSnapshot(
        pe_ratio=18.0,
        earnings_growth_rate_percent=24.0,
        peg_ratio=0.75,
        source="test",
    )

    indicators = service.build(quote, position, reference_levels, fundamentals)

    assert indicators.current_price == 180.0
    assert indicators.market_value == 1800.0
    assert indicators.unrealized_pnl == 300.0
    assert indicators.unrealized_pnl_percent == 20.0
    assert indicators.drawdown_from_52w_high_percent == 10.0
    assert indicators.drawdown_from_90d_high_percent == 5.26
    assert indicators.pe_ratio == 18.0
    assert indicators.earnings_growth_rate_percent == 24.0
    assert indicators.peg_ratio == 0.75
    assert indicators.valuation_label == ValuationLabel.UNDERVALUED


def test_indicator_service_enriches_position_from_quote():
    service = IndicatorService()
    position = PositionSnapshot(
        symbol="MSFT",
        quantity=2,
        average_cost=400.0,
        currency="USD",
    )
    quote = QuoteSnapshot(
        symbol="MSFT",
        last_price=410.0,
        previous_close=408.0,
        change_percent=0.49,
        source="test",
    )

    enriched = service.enrich_position(position, quote)

    assert enriched.market_price == 410.0
    assert enriched.market_value == 820.0
    assert enriched.unrealized_pnl == 20.0
    assert enriched.unrealized_pnl_percent == 2.5
