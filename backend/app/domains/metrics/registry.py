from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.core.types.common import AlertRuleMetric, AlertRuleOperator, AlertRuleSource
from app.domains.snapshot.schemas import CanonicalSnapshot, CanonicalWatchlistItem

MetricValueType = Literal["number", "text"]


@dataclass(frozen=True)
class MetricDefinition:
    metric: AlertRuleMetric
    source: AlertRuleSource
    label: str
    value_type: MetricValueType
    default_operator: AlertRuleOperator
    default_threshold: str
    unit: str = ""


@dataclass(frozen=True)
class MetricValue:
    raw: float | str
    display: str


class MetricRegistry:
    def __init__(self, definitions: list[MetricDefinition]) -> None:
        self._definitions = definitions
        self._by_key = {
            (definition.source, definition.metric): definition for definition in definitions
        }

    def definitions(self) -> list[MetricDefinition]:
        return list(self._definitions)

    def for_source(self, source: AlertRuleSource) -> list[MetricDefinition]:
        return [definition for definition in self._definitions if definition.source == source]

    def get(
        self,
        source: AlertRuleSource,
        metric: AlertRuleMetric,
    ) -> MetricDefinition | None:
        return self._by_key.get((source, metric))

    def resolve(
        self,
        snapshot: CanonicalSnapshot,
        source: AlertRuleSource,
        metric: AlertRuleMetric,
        symbol: str = "",
    ) -> MetricValue | None:
        definition = self.get(source, metric)
        if definition is None:
            return None

        if source == AlertRuleSource.WATCHLIST:
            item = self._find_watchlist_item(snapshot, symbol)
            if item is None or item.indicators is None:
                return None
            value = self._watchlist_value(item, metric)
            return self._format_value(value, definition)

        if source == AlertRuleSource.PORTFOLIO:
            value = self._portfolio_value(snapshot, metric)
            return self._format_value(value, definition)

        return None

    def _find_watchlist_item(
        self,
        snapshot: CanonicalSnapshot,
        symbol: str,
    ) -> CanonicalWatchlistItem | None:
        normalized = symbol.strip().upper()
        return next((item for item in snapshot.watchlist if item.symbol == normalized), None)

    def _watchlist_value(
        self,
        item: CanonicalWatchlistItem,
        metric: AlertRuleMetric,
    ) -> float | str | None:
        indicators = item.indicators
        if indicators is None:
            return None

        if metric == AlertRuleMetric.CURRENT_PRICE:
            return indicators.current_price
        if metric == AlertRuleMetric.DAY_CHANGE_PERCENT:
            return indicators.day_change_percent
        if metric == AlertRuleMetric.DRAWDOWN_52W:
            return indicators.drawdown_from_52w_high_percent
        if metric == AlertRuleMetric.DRAWDOWN_90D:
            return indicators.drawdown_from_90d_high_percent
        if metric == AlertRuleMetric.VALUATION_LABEL:
            return indicators.valuation_label.value if indicators.valuation_label else None
        return None

    def _portfolio_value(
        self,
        snapshot: CanonicalSnapshot,
        metric: AlertRuleMetric,
    ) -> float | None:
        if metric == AlertRuleMetric.NET_LIQUIDATION:
            return snapshot.account.net_liquidation
        if metric == AlertRuleMetric.AVAILABLE_FUNDS:
            return snapshot.account.available_funds
        if metric == AlertRuleMetric.BUYING_POWER:
            return snapshot.account.buying_power
        return None

    def _format_value(
        self,
        value: float | str | None,
        definition: MetricDefinition,
    ) -> MetricValue | None:
        if value is None:
            return None
        if isinstance(value, str):
            return MetricValue(raw=value, display=value)
        if definition.unit == "%":
            return MetricValue(raw=value, display=f"{value:.2f}%")
        return MetricValue(raw=value, display=f"{value:.2f}")


def get_alert_metric_registry() -> MetricRegistry:
    return MetricRegistry(
        [
            MetricDefinition(
                metric=AlertRuleMetric.CURRENT_PRICE,
                source=AlertRuleSource.WATCHLIST,
                label="当前价",
                value_type="number",
                default_operator=AlertRuleOperator.BELOW,
                default_threshold="",
            ),
            MetricDefinition(
                metric=AlertRuleMetric.DAY_CHANGE_PERCENT,
                source=AlertRuleSource.WATCHLIST,
                label="日内涨跌",
                value_type="number",
                default_operator=AlertRuleOperator.BELOW,
                default_threshold="-5",
                unit="%",
            ),
            MetricDefinition(
                metric=AlertRuleMetric.DRAWDOWN_52W,
                source=AlertRuleSource.WATCHLIST,
                label="52W 回撤",
                value_type="number",
                default_operator=AlertRuleOperator.ABOVE,
                default_threshold="5",
                unit="%",
            ),
            MetricDefinition(
                metric=AlertRuleMetric.DRAWDOWN_90D,
                source=AlertRuleSource.WATCHLIST,
                label="90D 回撤",
                value_type="number",
                default_operator=AlertRuleOperator.ABOVE,
                default_threshold="3",
                unit="%",
            ),
            MetricDefinition(
                metric=AlertRuleMetric.VALUATION_LABEL,
                source=AlertRuleSource.WATCHLIST,
                label="估值状态",
                value_type="text",
                default_operator=AlertRuleOperator.CHANGE_TO,
                default_threshold="undervalued",
            ),
            MetricDefinition(
                metric=AlertRuleMetric.NET_LIQUIDATION,
                source=AlertRuleSource.PORTFOLIO,
                label="账户净值",
                value_type="number",
                default_operator=AlertRuleOperator.BELOW,
                default_threshold="",
            ),
            MetricDefinition(
                metric=AlertRuleMetric.AVAILABLE_FUNDS,
                source=AlertRuleSource.PORTFOLIO,
                label="可用资金",
                value_type="number",
                default_operator=AlertRuleOperator.BELOW,
                default_threshold="",
            ),
            MetricDefinition(
                metric=AlertRuleMetric.BUYING_POWER,
                source=AlertRuleSource.PORTFOLIO,
                label="Buying Power",
                value_type="number",
                default_operator=AlertRuleOperator.BELOW,
                default_threshold="",
            ),
        ]
    )
