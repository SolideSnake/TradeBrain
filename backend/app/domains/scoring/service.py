from __future__ import annotations

from app.core.types.common import ValuationLabel
from app.domains.scoring.schemas import ScoreBreakdown, ScoreResult
from app.domains.snapshot.schemas import CanonicalWatchlistItem


class ScoringService:
    def score_item(self, item: CanonicalWatchlistItem) -> ScoreResult:
        breakdown: list[ScoreBreakdown] = []
        indicators = item.indicators
        if indicators is None:
            return ScoreResult(
                symbol=item.symbol,
                score=0,
                breakdown=[ScoreBreakdown(name="数据", score=0, reason="指标缺失")],
            )

        breakdown.append(self._score_valuation(indicators.valuation_label))
        breakdown.append(self._score_drawdown(indicators.drawdown_from_52w_high_percent))
        breakdown.append(self._score_day_change(indicators.day_change_percent))

        score = round(sum(part.score for part in breakdown), 2)
        return ScoreResult(symbol=item.symbol, score=min(score, 100), breakdown=breakdown)

    def _score_valuation(self, label: ValuationLabel | None) -> ScoreBreakdown:
        if label == ValuationLabel.UNDERVALUED:
            return ScoreBreakdown(name="估值", score=35, reason="估值状态为低估")
        if label == ValuationLabel.FAIR:
            return ScoreBreakdown(name="估值", score=18, reason="估值状态为合理")
        if label == ValuationLabel.OVERVALUED:
            return ScoreBreakdown(name="估值", score=0, reason="估值状态为高估")
        return ScoreBreakdown(name="估值", score=0, reason="估值状态缺失")

    def _score_drawdown(self, drawdown: float | None) -> ScoreBreakdown:
        if drawdown is None:
            return ScoreBreakdown(name="回撤", score=0, reason="52W 回撤缺失")
        if drawdown >= 20:
            return ScoreBreakdown(name="回撤", score=35, reason="52W 回撤超过 20%")
        if drawdown >= 10:
            return ScoreBreakdown(name="回撤", score=25, reason="52W 回撤超过 10%")
        if drawdown >= 5:
            return ScoreBreakdown(name="回撤", score=15, reason="52W 回撤超过 5%")
        return ScoreBreakdown(name="回撤", score=5, reason="52W 回撤较浅")

    def _score_day_change(self, change_percent: float | None) -> ScoreBreakdown:
        if change_percent is None:
            return ScoreBreakdown(name="波动", score=0, reason="日内涨跌缺失")
        if change_percent <= -5:
            return ScoreBreakdown(name="波动", score=30, reason="日跌幅超过 5%")
        if change_percent <= -3:
            return ScoreBreakdown(name="波动", score=20, reason="日跌幅超过 3%")
        if change_percent <= -1:
            return ScoreBreakdown(name="波动", score=10, reason="日跌幅超过 1%")
        return ScoreBreakdown(name="波动", score=0, reason="未出现明显日跌幅")
