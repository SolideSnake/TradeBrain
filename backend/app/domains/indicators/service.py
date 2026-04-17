from __future__ import annotations

from app.domains.fundamentals.schemas import FundamentalSnapshot
from app.domains.indicators.schemas import IndicatorSnapshot, PriceReferenceLevels
from app.domains.market.schemas import QuoteSnapshot
from app.domains.portfolio.schemas import PositionSnapshot
from app.domains.valuation.service import ValuationService


class IndicatorService:
    def __init__(self, valuation_service: ValuationService | None = None) -> None:
        self.valuation_service = valuation_service or ValuationService()

    def build(
        self,
        quote: QuoteSnapshot | None,
        position: PositionSnapshot | None,
        reference_levels: PriceReferenceLevels | None,
        fundamentals: FundamentalSnapshot | None = None,
    ) -> IndicatorSnapshot:
        current_price = self._resolve_current_price(quote, position)
        average_cost = position.average_cost if position else None
        market_value = None
        unrealized_pnl = None
        unrealized_pnl_percent = None

        if current_price is not None and position is not None:
            market_value = round(position.quantity * current_price, 2)
            if average_cost is not None:
                unrealized_pnl = round((current_price - average_cost) * position.quantity, 2)
                if average_cost != 0:
                    unrealized_pnl_percent = round(
                        ((current_price - average_cost) / average_cost) * 100,
                        2,
                    )

        high_52w = reference_levels.high_52w if reference_levels else None
        high_90d = reference_levels.high_90d if reference_levels else None

        return IndicatorSnapshot(
            current_price=current_price,
            previous_close=quote.previous_close if quote else None,
            day_change_percent=quote.change_percent if quote else None,
            average_cost=average_cost,
            market_value=market_value,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_percent=unrealized_pnl_percent,
            high_52w=high_52w,
            drawdown_from_52w_high_percent=self._calculate_drawdown(current_price, high_52w),
            high_90d=high_90d,
            drawdown_from_90d_high_percent=self._calculate_drawdown(current_price, high_90d),
            pe_ratio=fundamentals.pe_ratio if fundamentals else None,
            earnings_growth_rate_percent=(
                fundamentals.earnings_growth_rate_percent if fundamentals else None
            ),
            peg_ratio=fundamentals.peg_ratio if fundamentals else None,
            valuation_label=self.valuation_service.label_from_peg(
                fundamentals.peg_ratio if fundamentals else None
            ),
        )

    def enrich_position(
        self,
        position: PositionSnapshot,
        quote: QuoteSnapshot | None,
    ) -> PositionSnapshot:
        current_price = self._resolve_current_price(quote, position)
        if current_price is None:
            return position

        market_value = round(position.quantity * current_price, 2)
        unrealized_pnl = None
        unrealized_pnl_percent = None

        if position.average_cost is not None:
            unrealized_pnl = round((current_price - position.average_cost) * position.quantity, 2)
            if position.average_cost != 0:
                unrealized_pnl_percent = round(
                    ((current_price - position.average_cost) / position.average_cost) * 100,
                    2,
                )

        return position.model_copy(
            update={
                "market_price": current_price,
                "market_value": market_value,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_percent": unrealized_pnl_percent,
            }
        )

    def _resolve_current_price(
        self,
        quote: QuoteSnapshot | None,
        position: PositionSnapshot | None,
    ) -> float | None:
        if quote and quote.last_price is not None:
            return quote.last_price
        if position and position.market_price is not None:
            return position.market_price
        return None

    def _calculate_drawdown(
        self,
        current_price: float | None,
        reference_high: float | None,
    ) -> float | None:
        if current_price is None or reference_high in (None, 0):
            return None
        return round(((reference_high - current_price) / reference_high) * 100, 2)
