from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.core.types.common import AssetType, Market
from app.domains.market.schemas import QuoteSnapshot
from app.domains.portfolio.schemas import AccountSnapshot, PositionSnapshot


class SnapshotMeta(BaseModel):
    generated_at: datetime
    broker_mode: Literal["mock", "live"]
    broker_status: Literal["mock", "connected", "error"]
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


class BrokerSnapshotEnvelope(BaseModel):
    mode: Literal["mock", "live"]
    status: Literal["mock", "connected", "error"]
    account: AccountSnapshot
    positions: list[PositionSnapshot]
    quotes: dict[str, QuoteSnapshot]
    warnings: list[str] = Field(default_factory=list)


class CanonicalSnapshot(BaseModel):
    meta: SnapshotMeta
    summary: SnapshotSummary
    account: AccountSnapshot
    watchlist: list[CanonicalWatchlistItem]
    positions: list[PositionSnapshot]
