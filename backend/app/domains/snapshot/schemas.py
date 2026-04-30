from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.core.types.common import AssetType, Market
from app.domains.fundamentals.schemas import FundamentalSnapshot
from app.domains.fx.schemas import FxRateSnapshot
from app.domains.indicators.schemas import IndicatorSnapshot, PriceReferenceLevels
from app.domains.market.schemas import QuoteSnapshot
from app.domains.portfolio.schemas import AccountSnapshot, PositionSnapshot
from app.domains.state.schemas import WatchlistStateSnapshot


class SnapshotMeta(BaseModel):
    generated_at: datetime
    broker_mode: Literal["mock", "live"]
    broker_status: Literal["mock", "connected", "error"]
    broker_profile: Literal["mock", "real", "paper"] = "mock"
    broker_display_name: str = "Mock 数据"
    warnings: list[str] = Field(default_factory=list)


class SnapshotSummary(BaseModel):
    tracked_symbols: int
    enabled_symbols: int
    symbols_in_position: int
    quote_coverage: int
    position_count: int


class CanonicalWatchlistItem(BaseModel):
    id: int
    symbol: str
    name: str
    market: Market
    asset_type: AssetType
    group_name: str
    enabled: bool
    in_position: bool
    notes: str
    quote: QuoteSnapshot | None = None
    position: PositionSnapshot | None = None
    reference_levels: PriceReferenceLevels | None = None
    fundamentals: FundamentalSnapshot | None = None
    indicators: IndicatorSnapshot | None = None
    state: WatchlistStateSnapshot | None = None


class BrokerSnapshotEnvelope(BaseModel):
    mode: Literal["mock", "live"]
    status: Literal["mock", "connected", "error"]
    profile: Literal["mock", "real", "paper"] = "mock"
    display_name: str = "Mock 数据"
    account: AccountSnapshot
    positions: list[PositionSnapshot]
    quotes: dict[str, QuoteSnapshot]
    reference_levels: dict[str, PriceReferenceLevels]
    fundamentals: dict[str, FundamentalSnapshot]
    fx_rates: dict[str, FxRateSnapshot] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class CanonicalSnapshot(BaseModel):
    meta: SnapshotMeta
    summary: SnapshotSummary
    account: AccountSnapshot
    watchlist: list[CanonicalWatchlistItem]
    positions: list[PositionSnapshot]


class SnapshotResponse(BaseModel):
    snapshot: CanonicalSnapshot | None = None
    cache_status: Literal["empty", "idle", "refreshing", "success", "failed"]
    from_cache: bool
    last_success_at: datetime | None = None
    refresh_started_at: datetime | None = None
    last_error_at: datetime | None = None
    last_error: str = ""
