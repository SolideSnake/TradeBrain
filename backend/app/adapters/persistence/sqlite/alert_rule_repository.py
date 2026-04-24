from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.types.common import AlertDeliveryStatus
from app.domains.alerting.models import AlertRule
from app.domains.alerting.schemas import AlertRuleCreate, AlertRuleUpdate


class AlertRuleRepository:
    def list(self, db: Session) -> list[AlertRule]:
        query = select(AlertRule).order_by(AlertRule.enabled.desc(), AlertRule.created_at.desc())
        return list(db.scalars(query))

    def list_enabled(self, db: Session) -> list[AlertRule]:
        query = select(AlertRule).where(AlertRule.enabled.is_(True)).order_by(AlertRule.created_at.asc())
        return list(db.scalars(query))

    def get(self, db: Session, rule_id: int) -> AlertRule | None:
        return db.get(AlertRule, rule_id)

    def create(self, db: Session, payload: AlertRuleCreate) -> AlertRule:
        rule = AlertRule(**payload.model_dump())
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule

    def update(self, db: Session, rule: AlertRule, payload: AlertRuleUpdate) -> AlertRule:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(rule, field, value)
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule

    def delete(self, db: Session, rule: AlertRule) -> None:
        db.delete(rule)
        db.commit()

    def record_delivery(
        self,
        db: Session,
        rule: AlertRule,
        delivery_status: AlertDeliveryStatus,
        occurred_at: datetime,
        error_detail: str,
    ) -> None:
        rule.last_triggered_at = occurred_at
        if delivery_status == AlertDeliveryStatus.SENT:
            rule.sent_count += 1
            rule.last_sent_at = occurred_at
            rule.last_error = ""
        else:
            rule.failed_count += 1
            rule.last_failed_at = occurred_at
            rule.last_error = error_detail
        db.add(rule)

    def record_evaluation(
        self,
        db: Session,
        rule: AlertRule,
        *,
        evaluated_at: datetime,
        observed_value: str,
        matched: bool,
        should_notify: bool,
        suppression_reason: str,
    ) -> None:
        rule.last_evaluated_at = evaluated_at
        rule.last_observed_value = observed_value
        rule.last_matched = matched
        if matched and not should_notify and suppression_reason:
            rule.suppressed_count += 1
            rule.last_suppressed_at = evaluated_at
        db.add(rule)

    def reset_all_counters(self, db: Session) -> None:
        for rule in self.list(db):
            rule.sent_count = 0
            rule.failed_count = 0
            rule.suppressed_count = 0
            rule.last_sent_at = None
            rule.last_failed_at = None
            rule.last_suppressed_at = None
            rule.last_error = ""
            db.add(rule)
        db.commit()
