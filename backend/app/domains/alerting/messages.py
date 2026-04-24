from __future__ import annotations

from app.core.types.common import ValuationLabel
from app.domains.alerting.models import AlertRule
from app.domains.indicators.schemas import IndicatorSnapshot
from app.domains.metrics import MetricRegistry, get_alert_metric_registry
from app.domains.state.schemas import WatchlistStateSnapshot


class AlertMessageBuilder:
    def __init__(self, metric_registry: MetricRegistry | None = None) -> None:
        self.metric_registry = metric_registry or get_alert_metric_registry()

    def build_state_change_message(
        self,
        symbol: str,
        state: WatchlistStateSnapshot,
        indicator: IndicatorSnapshot | None,
    ) -> str:
        lines = [
            f"{symbol} 估值状态变化",
            f"状态: {self.label_text(state.previous_label)} -> {self.label_text(state.current_label)}",
        ]

        if indicator and indicator.peg_ratio is not None:
            lines.append(f"PEG: {indicator.peg_ratio:.2f}")
        if indicator and indicator.pe_ratio is not None:
            lines.append(f"PE: {indicator.pe_ratio:.2f}")
        if indicator and indicator.earnings_growth_rate_percent is not None:
            lines.append(f"增长率: {indicator.earnings_growth_rate_percent:.2f}%")
        lines.append(f"时间: {state.evaluated_at.isoformat()}")
        return "\n".join(lines)

    def label_text(self, label: ValuationLabel | None) -> str:
        mapping = {
            ValuationLabel.UNDERVALUED: "低估",
            ValuationLabel.FAIR: "合理",
            ValuationLabel.OVERVALUED: "高估",
        }
        return mapping.get(label, "--")

    def build_rule_message(self, rule: AlertRule, observed_value: str) -> str:
        if (rule.message_template or "").strip():
            return self._render_template(rule, observed_value)

        return "\n".join(
            [
                f"{rule.name}",
                f"规则: {self.metric_text(rule.metric)} {self.operator_text(rule.operator)} {self.threshold_text(rule.threshold_value)}",
                f"当前值: {observed_value}",
            ]
        )

    def metric_text(self, metric) -> str:
        key = getattr(metric, "value", metric)
        for definition in self.metric_registry.definitions():
            if definition.metric.value == str(key):
                return definition.label
        return str(key)

    def operator_text(self, operator) -> str:
        key = getattr(operator, "value", operator)
        mapping = {
            "above": "高于",
            "below": "低于",
            "equals": "等于",
            "becomes": "变为",
            "gte": "大于等于",
            "lte": "小于等于",
            "not_equals": "不等于",
            "cross_above": "上穿",
            "cross_below": "下穿",
            "change_to": "变为",
        }
        return mapping.get(str(key), str(key))

    def threshold_text(self, value: str) -> str:
        mapping = {
            "undervalued": "低估",
            "fair": "合理",
            "overvalued": "高估",
        }
        return mapping.get(value, value)

    def _render_template(self, rule: AlertRule, observed_value: str) -> str:
        values = {
            "name": rule.name,
            "symbol": rule.symbol or "ACCOUNT",
            "metric": self.metric_text(rule.metric),
            "operator": self.operator_text(rule.operator),
            "threshold": self.threshold_text(rule.threshold_value),
            "observed_value": observed_value,
        }
        message = rule.message_template
        for key, value in values.items():
            message = message.replace(f"{{{{{key}}}}}", value)
        return message
