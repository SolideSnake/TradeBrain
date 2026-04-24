from __future__ import annotations

from sqlalchemy.orm import Session

from app.adapters.persistence.sqlite.alert_rule_repository import AlertRuleRepository
from app.adapters.persistence.sqlite.alert_repository import AlertRepository
from app.adapters.telegram.client import TelegramNotifier, create_telegram_notifier
from app.application.notification_settings_service import NotificationSettingsService
from app.core.types.common import AlertChannel, AlertDeliveryStatus, AlertLevel
from app.domains.alerting.rules import AlertRuleEngine
from app.domains.alerting.schemas import AlertCandidate
from app.domains.alerts.schemas import AlertEventRead
from app.domains.preferences.schemas import NotificationTestResult
from app.domains.snapshot.schemas import CanonicalSnapshot


class NotificationService:
    def __init__(
        self,
        alert_repository: AlertRepository | None = None,
        alert_rule_repository: AlertRuleRepository | None = None,
        rule_engine: AlertRuleEngine | None = None,
        notifier: TelegramNotifier | None = None,
        notification_settings_service: NotificationSettingsService | None = None,
    ) -> None:
        self.alert_repository = alert_repository or AlertRepository()
        self.alert_rule_repository = alert_rule_repository or AlertRuleRepository()
        self.rule_engine = rule_engine or AlertRuleEngine()
        self.notifier = notifier
        self.notification_settings_service = notification_settings_service or NotificationSettingsService()

    def handle_snapshot(
        self,
        db: Session,
        snapshot: CanonicalSnapshot,
    ) -> list[AlertEventRead]:
        rules = self.alert_rule_repository.list_enabled(db)
        evaluated_at = self._now()
        evaluations = self.rule_engine.evaluate_snapshot(snapshot, rules, evaluated_at)
        rules_by_id = {rule.id: rule for rule in rules}

        candidates: list[AlertCandidate] = []
        for evaluation in evaluations:
            rule = rules_by_id.get(evaluation.rule_id)
            if rule is None:
                continue
            self.alert_rule_repository.record_evaluation(
                db,
                rule,
                evaluated_at=evaluated_at,
                observed_value=evaluation.observed_value,
                matched=evaluation.matched,
                should_notify=evaluation.should_notify,
                suppression_reason=evaluation.suppression_reason,
            )
            if evaluation.candidate is not None:
                candidates.append(evaluation.candidate)

        if not candidates:
            db.commit()
            return []

        return self.send_alerts(db, candidates)

    def send_alerts(
        self,
        db: Session,
        candidates: list[AlertCandidate],
    ) -> list[AlertEventRead]:
        if not candidates:
            return []

        events: list[AlertEventRead] = []
        telegram_notifier: TelegramNotifier | None = None

        for candidate in candidates:
            error_detail = ""
            delivery_status = AlertDeliveryStatus.SKIPPED
            try:
                if candidate.channel == AlertChannel.TELEGRAM:
                    telegram_notifier = telegram_notifier or self._resolve_telegram_notifier(db)
                    result = telegram_notifier.send_message(candidate.message)
                    delivery_status = AlertDeliveryStatus(result.status)
                    if delivery_status == AlertDeliveryStatus.SKIPPED:
                        error_detail = "Telegram configuration is incomplete or delivery was skipped."
                else:
                    delivery_status = AlertDeliveryStatus.SKIPPED
                    error_detail = f"Unsupported alert channel: {candidate.channel}"
            except Exception as exc:
                delivery_status = AlertDeliveryStatus.FAILED
                error_detail = str(exc)

            rule = (
                self.alert_rule_repository.get(db, candidate.rule_id)
                if candidate.rule_id is not None
                else None
            )
            if rule is not None:
                self.alert_rule_repository.record_delivery(
                    db,
                    rule,
                    delivery_status,
                    self._now(),
                    error_detail,
                )

            event = self._create_event(
                db,
                symbol=candidate.symbol,
                channel=candidate.channel,
                level=candidate.level,
                delivery_status=delivery_status,
                title=candidate.title,
                message=candidate.message,
                error_detail=error_detail,
            )
            events.append(event)

        db.commit()
        return events

    def send_test_notification(self, db: Session) -> NotificationTestResult:
        bot_token, chat_id = self.notification_settings_service.resolve_telegram_credentials(db)
        message = "TradeBrain Telegram 测试消息\n如果你收到这条消息，说明当前保存的 Telegram 配置可用。"

        if not bot_token or not chat_id:
            self._create_event(
                db,
                symbol="SYSTEM",
                channel=AlertChannel.TELEGRAM,
                level=AlertLevel.INFO,
                delivery_status=AlertDeliveryStatus.SKIPPED,
                title="Telegram 测试消息",
                message="Telegram test skipped: missing bot token or chat id.",
                error_detail="Telegram configuration is incomplete.",
            )
            db.commit()
            return NotificationTestResult(
                success=False,
                delivery_status=AlertDeliveryStatus.SKIPPED,
                detail="请先保存完整的 Telegram Bot Token 和 Chat ID。",
            )

        error_detail = ""
        detail = "测试消息已发送。请检查 Telegram。"

        try:
            notifier = self._resolve_telegram_notifier(db)
            result = notifier.send_message(message)
            delivery_status = AlertDeliveryStatus(result.status)
            if delivery_status == AlertDeliveryStatus.SKIPPED:
                error_detail = "Telegram configuration is incomplete or delivery was skipped."
                detail = "测试消息未发送。"
        except Exception as exc:
            delivery_status = AlertDeliveryStatus.FAILED
            detail = "测试消息发送失败。"
            error_detail = str(exc)

        self._create_event(
            db,
            symbol="SYSTEM",
            channel=AlertChannel.TELEGRAM,
            level=AlertLevel.INFO,
            delivery_status=delivery_status,
            title="Telegram 测试消息",
            message=message,
            error_detail=error_detail,
        )
        db.commit()

        return NotificationTestResult(
            success=delivery_status == AlertDeliveryStatus.SENT,
            delivery_status=delivery_status,
            detail=detail if not error_detail else f"{detail} {error_detail}",
        )

    def list_recent(self, db: Session, limit: int = 50) -> list[AlertEventRead]:
        return [
            AlertEventRead.model_validate(event, from_attributes=True)
            for event in self.alert_repository.list_recent(db, limit)
        ]

    def _resolve_telegram_notifier(self, db: Session) -> TelegramNotifier:
        if self.notifier is not None:
            return self.notifier

        bot_token, chat_id = self.notification_settings_service.resolve_telegram_credentials(db)
        return create_telegram_notifier(bot_token, chat_id)

    def _create_event(self, db: Session, **payload) -> AlertEventRead:
        event = self.alert_repository.create(db, **payload)
        db.flush()
        db.refresh(event)
        return AlertEventRead.model_validate(event, from_attributes=True)

    def _now(self):
        from datetime import UTC, datetime

        return datetime.now(UTC)
