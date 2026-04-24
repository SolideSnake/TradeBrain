from __future__ import annotations

from datetime import UTC, datetime

from app.core.types.common import ScannerCandidateReason, ValuationLabel
from app.domains.scanner.schemas import ScannerCandidate, ScannerResult
from app.domains.scoring import ScoringService
from app.domains.snapshot.schemas import CanonicalSnapshot, CanonicalWatchlistItem
from app.domains.strategy import StrategyEvaluator, StrategyRule


class ScannerService:
    def __init__(
        self,
        scoring_service: ScoringService | None = None,
        strategy_evaluator: StrategyEvaluator | None = None,
    ) -> None:
        self.scoring_service = scoring_service or ScoringService()
        self.strategy_evaluator = strategy_evaluator or StrategyEvaluator()

    def scan_snapshot(
        self,
        snapshot: CanonicalSnapshot,
        strategy_rule: StrategyRule | None = None,
    ) -> ScannerResult:
        rule = strategy_rule or self.default_rule()
        candidates = [
            candidate
            for item in snapshot.watchlist
            if item.enabled
            for candidate in [self._candidate_for_item(item, rule)]
            if candidate is not None
        ]
        candidates.sort(key=lambda candidate: candidate.score.score, reverse=True)
        return ScannerResult(generated_at=datetime.now(UTC), candidates=candidates)

    def default_rule(self) -> StrategyRule:
        return StrategyRule(
            id="default_pullback_value",
            name="默认回撤估值观察",
            max_peg=1.5,
            min_drawdown_52w_percent=5,
        )

    def _candidate_for_item(
        self,
        item: CanonicalWatchlistItem,
        rule: StrategyRule,
    ) -> ScannerCandidate | None:
        strategy = self.strategy_evaluator.evaluate(item, rule)
        score = self.scoring_service.score_item(item)
        reason = self._reason_for_item(item)
        if reason is None and not strategy.matched and score.score < 30:
            return None
        return ScannerCandidate(
            symbol=item.symbol,
            name=item.name,
            reason=reason or ScannerCandidateReason.PULLBACK_52W,
            score=score,
            strategy=strategy,
        )

    def _reason_for_item(
        self,
        item: CanonicalWatchlistItem,
    ) -> ScannerCandidateReason | None:
        indicators = item.indicators
        if indicators is None:
            return None
        if indicators.day_change_percent is not None and indicators.day_change_percent <= -5:
            return ScannerCandidateReason.LARGE_DROP
        if indicators.valuation_label == ValuationLabel.UNDERVALUED:
            return ScannerCandidateReason.UNDERVALUED
        if (
            indicators.drawdown_from_52w_high_percent is not None
            and indicators.drawdown_from_52w_high_percent >= 5
        ):
            return ScannerCandidateReason.PULLBACK_52W
        return None
