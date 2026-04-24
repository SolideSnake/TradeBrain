from __future__ import annotations

from datetime import UTC, datetime

from app.core.types.common import (
    AlertLevel,
    AlertRuleOperator,
    ValuationLabel,
)
from app.domains.alerting.messages import AlertMessageBuilder
from app.domains.alerting.models import AlertRule
from app.domains.alerting.schemas import AlertCandidate, AlertRuleEvaluation
from app.domains.metrics import MetricRegistry, get_alert_metric_registry
from app.domains.snapshot.schemas import CanonicalSnapshot


class AlertRuleEngine:
    def __init__(
        self,
        metric_registry: MetricRegistry | None = None,
        message_builder: AlertMessageBuilder | None = None,
    ) -> None:
        self.metric_registry = metric_registry or get_alert_metric_registry()
        self.message_builder = message_builder or AlertMessageBuilder(self.metric_registry)

    def evaluate_snapshot(
        self,
        snapshot: CanonicalSnapshot,
        rules: list[AlertRule],
        now: datetime | None = None,
    ) -> list[AlertRuleEvaluation]:
        evaluated_at = now or datetime.now(UTC)
        evaluations: list[AlertRuleEvaluation] = []

        for rule in rules:
            metric_value = self.metric_registry.resolve(
                snapshot,
                rule.source,
                rule.metric,
                rule.symbol,
            )
            if metric_value is None:
                evaluations.append(
                    AlertRuleEvaluation(
                        rule_id=rule.id,
                        observed_value="",
                        matched=False,
                        should_notify=False,
                        suppression_reason="metric_unavailable",
                    )
                )
                continue

            matched = self._matches(rule, metric_value.raw)
            should_notify, suppression_reason = self._notification_decision(
                rule,
                metric_value.raw,
                matched,
                evaluated_at,
            )
            candidate = None
            if should_notify:
                candidate = AlertCandidate(
                    rule_id=rule.id,
                    symbol=rule.symbol or "ACCOUNT",
                    level=AlertLevel.INFO,
                    title=rule.name,
                    message=self.message_builder.build_rule_message(
                        rule,
                        metric_value.display,
                    ),
                )

            evaluations.append(
                AlertRuleEvaluation(
                    rule_id=rule.id,
                    observed_value=str(metric_value.raw),
                    matched=matched,
                    should_notify=should_notify,
                    suppression_reason=suppression_reason,
                    candidate=candidate,
                )
            )

        return evaluations

    def _notification_decision(
        self,
        rule: AlertRule,
        observed: float | str,
        matched: bool,
        now: datetime,
    ) -> tuple[bool, str]:
        if not matched:
            return False, ""

        if self._in_cooldown(rule, now):
            return False, "cooldown"

        if rule.operator in {AlertRuleOperator.CROSS_ABOVE, AlertRuleOperator.CROSS_BELOW}:
            return True, ""

        if rule.operator in {AlertRuleOperator.BECOMES, AlertRuleOperator.CHANGE_TO}:
            previous = self._normalize_text(rule.last_observed_value)
            if not previous:
                return False, "arming_change_rule"
            return True, ""

        edge_only = True if rule.edge_only is None else rule.edge_only
        if edge_only and rule.last_matched:
            return False, "condition_already_matched"

        return True, ""

    def _matches(self, rule: AlertRule, observed: float | str) -> bool:
        if isinstance(observed, str):
            return self._matches_text(rule, observed)
        return self._matches_number(rule, observed)

    def _matches_number(self, rule: AlertRule, observed: float) -> bool:
        threshold = self._threshold_float(rule.threshold_value)
        if threshold is None:
            return False

        if rule.operator == AlertRuleOperator.ABOVE:
            return observed > threshold
        if rule.operator == AlertRuleOperator.BELOW:
            return observed < threshold
        if rule.operator == AlertRuleOperator.GTE:
            return observed >= threshold
        if rule.operator == AlertRuleOperator.LTE:
            return observed <= threshold
        if rule.operator == AlertRuleOperator.EQUALS:
            return observed == threshold
        if rule.operator == AlertRuleOperator.NOT_EQUALS:
            return observed != threshold
        if rule.operator == AlertRuleOperator.CROSS_ABOVE:
            previous = self._threshold_float(rule.last_observed_value)
            return previous is not None and previous <= threshold < observed
        if rule.operator == AlertRuleOperator.CROSS_BELOW:
            previous = self._threshold_float(rule.last_observed_value)
            return previous is not None and previous >= threshold > observed
        return False

    def _matches_text(self, rule: AlertRule, observed: str) -> bool:
        threshold = self._normalize_text_threshold(rule.threshold_value)
        observed_value = self._normalize_text(observed)

        if rule.operator == AlertRuleOperator.EQUALS:
            return observed_value == threshold
        if rule.operator == AlertRuleOperator.NOT_EQUALS:
            return observed_value != threshold
        if rule.operator in {AlertRuleOperator.BECOMES, AlertRuleOperator.CHANGE_TO}:
            previous = self._normalize_text(rule.last_observed_value)
            return observed_value == threshold and previous != threshold
        return False

    def _in_cooldown(self, rule: AlertRule, now: datetime) -> bool:
        if not rule.cooldown_seconds or rule.cooldown_seconds <= 0:
            return False
        last_delivery = self._latest_datetime(rule.last_sent_at, rule.last_failed_at)
        if last_delivery is None:
            return False
        return (self._aware(now) - self._aware(last_delivery)).total_seconds() < rule.cooldown_seconds

    def _latest_datetime(
        self,
        left: datetime | None,
        right: datetime | None,
    ) -> datetime | None:
        values = [value for value in [left, right] if value is not None]
        if not values:
            return None
        return max(values, key=self._aware)

    def _aware(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

    def _normalize_text_threshold(self, value: str) -> str:
        mapping = {
            "低估": ValuationLabel.UNDERVALUED.value,
            "合理": ValuationLabel.FAIR.value,
            "高估": ValuationLabel.OVERVALUED.value,
        }
        return mapping.get(value.strip(), value.strip()).lower()

    def _normalize_text(self, value: str | None) -> str:
        return (value or "").strip().lower()

    def _threshold_float(self, value: str | None) -> float | None:
        try:
            return float(value or "")
        except ValueError:
            return None
