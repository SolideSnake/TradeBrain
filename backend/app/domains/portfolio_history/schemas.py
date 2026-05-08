from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


PortfolioHistoryRange = Literal["1D", "1W", "1M", "YTD"]
PortfolioHistoryProfile = Literal["real", "paper"]


class PortfolioHistoryPointRead(BaseModel):
    recorded_at: datetime
    account_id: str
    broker_profile: PortfolioHistoryProfile
    currency: str
    net_liquidation: float | None = None
    cash_balance: float | None = None
    available_funds: float | None = None
    buying_power: float | None = None
    unrealized_pnl: float | None = None
    positions_market_value: float | None = None
