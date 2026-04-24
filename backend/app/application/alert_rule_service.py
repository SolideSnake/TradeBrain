from __future__ import annotations

from sqlalchemy.orm import Session

from app.adapters.persistence.sqlite.alert_rule_repository import AlertRuleRepository
from app.core.types.common import AlertRuleOperator, AlertRuleSource
from app.domains.alerting.models import AlertRule
from app.domains.alerting.schemas import (
    AlertRuleCreate,
    AlertRuleMetadataRead,
    AlertRuleMetricOption,
    AlertRuleOption,
    AlertRuleRead,
    AlertRuleTemplate,
    AlertRuleUpdate,
)
from app.domains.metrics import MetricRegistry, get_alert_metric_registry


class AlertRuleService:
    def __init__(
        self,
        repository: AlertRuleRepository | None = None,
        metric_registry: MetricRegistry | None = None,
    ) -> None:
        self.repository = repository or AlertRuleRepository()
        self.metric_registry = metric_registry or get_alert_metric_registry()

    def get_metadata(self) -> AlertRuleMetadataRead:
        return AlertRuleMetadataRead(
            sources=[
                AlertRuleOption(value=AlertRuleSource.WATCHLIST.value, label="追踪数据"),
                AlertRuleOption(value=AlertRuleSource.PORTFOLIO.value, label="资产数据"),
            ],
            operators=[
                AlertRuleOption(value=AlertRuleOperator.ABOVE.value, label="高于"),
                AlertRuleOption(value=AlertRuleOperator.BELOW.value, label="低于"),
                AlertRuleOption(value=AlertRuleOperator.GTE.value, label="大于等于"),
                AlertRuleOption(value=AlertRuleOperator.LTE.value, label="小于等于"),
                AlertRuleOption(value=AlertRuleOperator.EQUALS.value, label="等于"),
                AlertRuleOption(value=AlertRuleOperator.NOT_EQUALS.value, label="不等于"),
                AlertRuleOption(value=AlertRuleOperator.CROSS_ABOVE.value, label="上穿"),
                AlertRuleOption(value=AlertRuleOperator.CROSS_BELOW.value, label="下穿"),
                AlertRuleOption(value=AlertRuleOperator.CHANGE_TO.value, label="变为"),
            ],
            metrics=[
                AlertRuleMetricOption(
                    value=definition.metric.value,
                    label=definition.label,
                    source=definition.source,
                    value_type=definition.value_type,
                    default_operator=definition.default_operator,
                    default_threshold=definition.default_threshold,
                    unit=definition.unit,
                )
                for definition in self.metric_registry.definitions()
            ],
            templates=self._templates(),
        )

    def list_rules(self, db: Session) -> list[AlertRuleRead]:
        return [
            AlertRuleRead.model_validate(rule, from_attributes=True)
            for rule in self.repository.list(db)
        ]

    def create_rule(self, db: Session, payload: AlertRuleCreate) -> AlertRuleRead:
        rule = self.repository.create(db, payload)
        return AlertRuleRead.model_validate(rule, from_attributes=True)

    def update_rule(
        self,
        db: Session,
        rule_id: int,
        payload: AlertRuleUpdate,
    ) -> AlertRuleRead | None:
        rule = self.repository.get(db, rule_id)
        if rule is None:
            return None
        updated = self.repository.update(db, rule, payload)
        return AlertRuleRead.model_validate(updated, from_attributes=True)

    def delete_rule(self, db: Session, rule_id: int) -> bool:
        rule = self.repository.get(db, rule_id)
        if rule is None:
            return False
        self.repository.delete(db, rule)
        return True

    def reset_all_counters(self, db: Session) -> list[AlertRuleRead]:
        self.repository.reset_all_counters(db)
        return self.list_rules(db)

    def list_enabled_rules(self, db: Session) -> list[AlertRule]:
        return self.repository.list_enabled(db)

    def _templates(self) -> list[AlertRuleTemplate]:
        return [
            AlertRuleTemplate(
                id="price_above",
                label="价格高于",
                description="标的当前价高于指定价格时提醒。",
                source=AlertRuleSource.WATCHLIST,
                metric="current_price",
                operator="above",
                threshold_value="",
            ),
            AlertRuleTemplate(
                id="price_below",
                label="价格低于",
                description="标的当前价低于指定价格时提醒。",
                source=AlertRuleSource.WATCHLIST,
                metric="current_price",
                operator="below",
                threshold_value="",
            ),
            AlertRuleTemplate(
                id="drawdown_52w_above",
                label="52W 回撤高于",
                description="标的距离 52 周高点的回撤超过阈值时提醒。",
                source=AlertRuleSource.WATCHLIST,
                metric="drawdown_52w",
                operator="above",
                threshold_value="5",
            ),
            AlertRuleTemplate(
                id="day_drop_below",
                label="日跌幅超过",
                description="标的日内跌幅超过阈值时提醒，例如 -5%。",
                source=AlertRuleSource.WATCHLIST,
                metric="day_change_percent",
                operator="below",
                threshold_value="-5",
            ),
            AlertRuleTemplate(
                id="net_liquidation_below",
                label="账户净值低于",
                description="账户净值低于指定金额时提醒。",
                source=AlertRuleSource.PORTFOLIO,
                metric="net_liquidation",
                operator="below",
                threshold_value="",
            ),
            AlertRuleTemplate(
                id="available_funds_below",
                label="可用资金低于",
                description="可用资金低于指定金额时提醒。",
                source=AlertRuleSource.PORTFOLIO,
                metric="available_funds",
                operator="below",
                threshold_value="",
            ),
        ]
