from __future__ import annotations

from app.domains.snapshot.schemas import CanonicalWatchlistItem
from app.domains.strategy.schemas import StrategyEvaluation, StrategyRule


class StrategyEvaluator:
    def evaluate(
        self,
        item: CanonicalWatchlistItem,
        rule: StrategyRule,
    ) -> StrategyEvaluation:
        indicators = item.indicators
        if indicators is None:
            return StrategyEvaluation(
                rule_id=rule.id,
                rule_name=rule.name,
                matched=False,
                reasons=["指标缺失"],
            )

        checks: list[tuple[bool, str]] = []
        if rule.max_peg is not None:
            peg = indicators.peg_ratio
            checks.append((
                peg is not None and peg <= rule.max_peg,
                f"PEG <= {rule.max_peg}",
            ))
        if rule.min_drawdown_52w_percent is not None:
            drawdown = indicators.drawdown_from_52w_high_percent
            checks.append((
                drawdown is not None and drawdown >= rule.min_drawdown_52w_percent,
                f"52W 回撤 >= {rule.min_drawdown_52w_percent}%",
            ))
        if rule.min_day_drop_percent is not None:
            change = indicators.day_change_percent
            checks.append((
                change is not None and change <= -abs(rule.min_day_drop_percent),
                f"日跌幅 >= {abs(rule.min_day_drop_percent)}%",
            ))

        matched = bool(checks) and all(result for result, _reason in checks)
        reasons = [reason for result, reason in checks if result]
        return StrategyEvaluation(
            rule_id=rule.id,
            rule_name=rule.name,
            matched=matched,
            reasons=reasons,
        )
