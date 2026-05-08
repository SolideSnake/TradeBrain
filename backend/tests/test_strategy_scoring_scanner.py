from datetime import UTC, datetime

from app.core.types.common import (
    AssetType,
    Market,
    ScannerCandidateReason,
    ValuationLabel,
)
from app.domains.indicators.schemas import IndicatorSnapshot
from app.domains.scanner import ScannerService
from app.domains.scoring import ScoringService
from app.domains.snapshot.schemas import (
    CanonicalSnapshot,
    CanonicalWatchlistItem,
    SnapshotMeta,
    SnapshotSummary,
)
from app.domains.strategy import StrategyEvaluator, StrategyRule
from app.domains.portfolio.schemas import AccountSnapshot


def build_item(
    symbol: str = "NVDA",
    *,
    peg: float | None = 1.2,
    drawdown: float | None = 8.0,
    day_change: float | None = -2.0,
    label: ValuationLabel | None = ValuationLabel.UNDERVALUED,
) -> CanonicalWatchlistItem:
    return CanonicalWatchlistItem(
        id=1,
        symbol=symbol,
        name=f"{symbol} Corp",
        market=Market.US,
        asset_type=AssetType.STOCK,
        group_name="default",
        enabled=True,
        in_position=False,
        notes="",
        indicators=IndicatorSnapshot(
            current_price=100,
            day_change_percent=day_change,
            drawdown_from_52w_high_percent=drawdown,
            peg_ratio=peg,
            valuation_label=label,
        ),
    )


def build_snapshot(items: list[CanonicalWatchlistItem]) -> CanonicalSnapshot:
    now = datetime.now(UTC)
    return CanonicalSnapshot(
        meta=SnapshotMeta(
            generated_at=now,
            broker_mode="live",
            broker_status="connected",
            broker_profile="paper",
        ),
        summary=SnapshotSummary(
            tracked_symbols=len(items),
            enabled_symbols=len(items),
            symbols_in_position=0,
            quote_coverage=0,
            position_count=0,
        ),
        account=AccountSnapshot(
            account_id="MOCK",
            net_liquidation=100000,
            available_funds=50000,
            buying_power=100000,
            source="test",
            updated_at=now,
        ),
        watchlist=items,
        positions=[],
    )


def test_strategy_evaluator_matches_pullback_value_rule():
    rule = StrategyRule(
        id="pullback_value",
        name="回撤估值观察",
        max_peg=1.5,
        min_drawdown_52w_percent=5,
    )

    result = StrategyEvaluator().evaluate(build_item(), rule)

    assert result.matched is True
    assert "PEG <= 1.5" in result.reasons
    assert "52W 回撤 >= 5.0%" in result.reasons


def test_scoring_service_returns_bounded_breakdown():
    result = ScoringService().score_item(build_item(day_change=-6, drawdown=21))

    assert result.symbol == "NVDA"
    assert result.score == 100
    assert [part.name for part in result.breakdown] == ["估值", "回撤", "波动"]


def test_scanner_service_sorts_candidates_by_score():
    snapshot = build_snapshot(
        [
            build_item("LOW", peg=2.2, drawdown=1, day_change=0, label=ValuationLabel.OVERVALUED),
            build_item("HIGH", peg=1.1, drawdown=22, day_change=-6, label=ValuationLabel.UNDERVALUED),
        ]
    )

    result = ScannerService().scan_snapshot(snapshot)

    assert [candidate.symbol for candidate in result.candidates] == ["HIGH"]
    assert result.candidates[0].reason == ScannerCandidateReason.LARGE_DROP


def test_scanner_api_uses_latest_snapshot(client):
    client.post("/api/watchlist", json={"symbol": "AAPL"})
    snapshot_response = client.post("/api/snapshot/refresh")
    assert snapshot_response.status_code == 200

    response = client.get("/api/scanner")

    assert response.status_code == 200
    payload = response.json()
    assert "generated_at" in payload
    assert isinstance(payload["candidates"], list)
