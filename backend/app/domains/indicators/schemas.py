from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.core.types.common import ValuationLabel


class PriceReferenceLevels(BaseModel):
    high_52w: float | None = None
    low_52w: float | None = None
    high_90d: float | None = None
    low_90d: float | None = None
    source: str = "unknown"
    as_of: datetime | None = None


class IndicatorSnapshot(BaseModel):
    current_price: float | None = None
    current_price_base: float | None = None
    previous_close: float | None = None
    previous_close_base: float | None = None
    day_change_percent: float | None = None
    average_cost: float | None = None
    market_value: float | None = None
    unrealized_pnl: float | None = None
    unrealized_pnl_percent: float | None = None
    high_52w: float | None = None
    low_52w: float | None = None
    drawdown_from_52w_high_percent: float | None = None
    gain_from_52w_low_percent: float | None = None
    high_90d: float | None = None
    low_90d: float | None = None
    drawdown_from_90d_high_percent: float | None = None
    gain_from_90d_low_percent: float | None = None
    pe_ratio: float | None = None
    earnings_growth_rate_percent: float | None = None
    peg_ratio: float | None = None
    valuation_label: ValuationLabel | None = None
