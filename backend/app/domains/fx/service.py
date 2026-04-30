from __future__ import annotations

from app.domains.fx.schemas import FxRateSnapshot
from app.domains.portfolio.schemas import PositionSnapshot


class FxConversionService:
    def convert_position(
        self,
        position: PositionSnapshot,
        base_currency: str,
        rates: dict[str, FxRateSnapshot],
    ) -> PositionSnapshot:
        source_currency = position.currency.strip().upper() or base_currency
        normalized_base = base_currency.strip().upper() or source_currency
        rate = self._resolve_rate(source_currency, normalized_base, rates)

        if rate is None:
            return position.model_copy(
                update={
                    "currency": source_currency,
                    "base_currency": normalized_base,
                    "fx_rate_to_base": None,
                    "average_cost_base": None,
                    "market_price_base": None,
                    "market_value_base": None,
                    "unrealized_pnl_base": None,
                }
            )

        return position.model_copy(
            update={
                "currency": source_currency,
                "base_currency": normalized_base,
                "fx_rate_to_base": rate,
                "average_cost_base": self._convert(position.average_cost, rate),
                "market_price_base": self._convert(position.market_price, rate),
                "market_value_base": self._convert(position.market_value, rate),
                "unrealized_pnl_base": self._convert(position.unrealized_pnl, rate),
            }
        )

    def _resolve_rate(
        self,
        source_currency: str,
        base_currency: str,
        rates: dict[str, FxRateSnapshot],
    ) -> float | None:
        if source_currency == base_currency:
            return 1.0
        rate = rates.get(source_currency)
        if rate is None:
            return None
        if rate.to_currency != base_currency:
            return None
        return rate.rate

    def _convert(self, value: float | None, rate: float) -> float | None:
        if value is None:
            return None
        return round(value * rate, 2)
