from __future__ import annotations

from sqlalchemy.orm import Session

from app.adapters.feishu.client import FeishuNotifier, create_feishu_notifier
from app.adapters.persistence.sqlite.alert_rule_repository import AlertRuleRepository
from app.adapters.telegram.client import TelegramNotifier, create_telegram_notifier
from app.application.event_service import EventService
from app.application.notification_settings_service import NotificationSettingsService
from app.core.types.common import AlertChannel, AlertDeliveryStatus, AlertLevel
from app.domains.alerting.rules import AlertRuleEngine
from app.domains.alerting.schemas import AlertCandidate
from app.domains.events.schemas import EventRecordRead
from app.domains.preferences.schemas import NotificationTestResult
from app.domains.snapshot.schemas import CanonicalSnapshot


class NotificationService:
    def __init__(
        self,
        event_service: EventService | None = None,
        alert_rule_repository: AlertRuleRepository | None = None,
        rule_engine: AlertRuleEngine | None = None,
        notifier: TelegramNotifier | None = None,
        feishu_notifier: FeishuNotifier | None = None,
        notification_settings_service: NotificationSettingsService | None = None,
    ) -> None:
        self.event_service = event_service or EventService()
        self.alert_rule_repository = alert_rule_repository or AlertRuleRepository()
        self.rule_engine = rule_engine or AlertRuleEngine()
        self.notifier = notifier
        self.feishu_notifier = feishu_notifier
        self.notification_settings_service = notification_settings_service or NotificationSettingsService()

    def handle_snapshot(
        self,
        db: Session,
        snapshot: CanonicalSnapshot,
    ) -> list[EventRecordRead]:
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
    ) -> list[EventRecordRead]:
        if not candidates:
            return []

        events: list[EventRecordRead] = []
        telegram_notifier: TelegramNotifier | None = None
        feishu_notifier: FeishuNotifier | None = None

        for candidate in candidates:
            for channel in self._resolve_delivery_channels(db, candidate):
                error_detail = ""
                delivery_status = AlertDeliveryStatus.SKIPPED
                try:
                    if channel == AlertChannel.TELEGRAM:
                        telegram_notifier = telegram_notifier or self._resolve_telegram_notifier(db)
                        result = telegram_notifier.send_message(candidate.message)
                        delivery_status = AlertDeliveryStatus(result.status)
                        if delivery_status == AlertDeliveryStatus.SKIPPED:
                            error_detail = "Telegram configuration is incomplete or delivery was skipped."
                    elif channel == AlertChannel.FEISHU:
                        feishu_notifier = feishu_notifier or self._resolve_feishu_notifier(db)
                        result = feishu_notifier.send_message(candidate.message)
                        delivery_status = AlertDeliveryStatus(result.status)
                        if delivery_status == AlertDeliveryStatus.SKIPPED:
                            error_detail = "Feishu webhook configuration is incomplete or delivery was skipped."
                    else:
                        delivery_status = AlertDeliveryStatus.SKIPPED
                        error_detail = f"Unsupported alert channel: {channel}"
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

                event = self._record_delivery_event(
                    db,
                    symbol=candidate.symbol,
                    channel=channel,
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
        channels = self._resolve_configured_channels(db)
        message = "TradeBrain 通知测试消息\n如果你收到这条消息，说明当前保存的通知配置可用。"

        if not channels:
            self._record_delivery_event(
                db,
                symbol="SYSTEM",
                channel=AlertChannel.TELEGRAM,
                level=AlertLevel.INFO,
                delivery_status=AlertDeliveryStatus.SKIPPED,
                title="通知测试消息",
                message="Notification test skipped: no delivery channel configured.",
                error_detail="请先保存 Telegram 或飞书配置。",
            )
            db.commit()
            return NotificationTestResult(
                success=False,
                delivery_status=AlertDeliveryStatus.SKIPPED,
                detail="请先保存 Telegram 或飞书配置。",
            )

        statuses: list[AlertDeliveryStatus] = []
        details: list[str] = []
        telegram_notifier: TelegramNotifier | None = None
        feishu_notifier: FeishuNotifier | None = None

        for channel in channels:
            error_detail = ""
            try:
                if channel == AlertChannel.TELEGRAM:
                    telegram_notifier = telegram_notifier or self._resolve_telegram_notifier(db)
                    result = telegram_notifier.send_message(message)
                elif channel == AlertChannel.FEISHU:
                    feishu_notifier = feishu_notifier or self._resolve_feishu_notifier(db)
                    result = feishu_notifier.send_message(message)
                else:
                    result = type("Result", (), {"status": "skipped"})()
                    error_detail = f"Unsupported alert channel: {channel}"
                delivery_status = AlertDeliveryStatus(result.status)
            except Exception as exc:
                delivery_status = AlertDeliveryStatus.FAILED
                error_detail = str(exc)

            statuses.append(delivery_status)
            details.append(f"{self._channel_label(channel)}: {delivery_status.value}")
            self._record_delivery_event(
                db,
                symbol="SYSTEM",
                channel=channel,
                level=AlertLevel.INFO,
                delivery_status=delivery_status,
                title=f"{self._channel_label(channel)} 测试消息",
                message=message,
                error_detail=error_detail,
            )

        db.commit()

        if all(status == AlertDeliveryStatus.SENT for status in statuses):
            delivery_status = AlertDeliveryStatus.SENT
            detail = "测试消息已发送。"
        elif any(status == AlertDeliveryStatus.FAILED for status in statuses):
            delivery_status = AlertDeliveryStatus.FAILED
            detail = "部分或全部测试消息发送失败。"
        else:
            delivery_status = AlertDeliveryStatus.SKIPPED
            detail = "测试消息未发送。"
        return NotificationTestResult(
            success=delivery_status == AlertDeliveryStatus.SENT,
            delivery_status=delivery_status,
            detail=f"{detail} {'; '.join(details)}",
        )

    def _resolve_telegram_notifier(self, db: Session) -> TelegramNotifier:
        if self.notifier is not None:
            return self.notifier

        bot_token, chat_id = self.notification_settings_service.resolve_telegram_credentials(db)
        return create_telegram_notifier(bot_token, chat_id)

    def _resolve_feishu_notifier(self, db: Session) -> FeishuNotifier:
        if self.feishu_notifier is not None:
            return self.feishu_notifier

        webhook_url, secret = self.notification_settings_service.resolve_feishu_credentials(db)
        return create_feishu_notifier(webhook_url, secret)

    def _resolve_delivery_channels(
        self,
        db: Session,
        candidate: AlertCandidate,
    ) -> list[AlertChannel]:
        if self.notifier is not None or self.feishu_notifier is not None:
            channels = []
            if self.notifier is not None:
                channels.append(AlertChannel.TELEGRAM)
            if self.feishu_notifier is not None:
                channels.append(AlertChannel.FEISHU)
            return channels

        channels = self._resolve_configured_channels(db)
        if channels:
            return channels
        return [candidate.channel]

    def _resolve_configured_channels(self, db: Session) -> list[AlertChannel]:
        settings = self.notification_settings_service.get_settings(db)
        channels: list[AlertChannel] = []
        if settings.telegram_enabled:
            channels.append(AlertChannel.TELEGRAM)
        if settings.feishu_enabled:
            channels.append(AlertChannel.FEISHU)
        return channels

    def _channel_label(self, channel: AlertChannel) -> str:
        if channel == AlertChannel.TELEGRAM:
            return "Telegram"
        if channel == AlertChannel.FEISHU:
            return "飞书"
        return str(channel)

    def _record_delivery_event(
        self,
        db: Session,
        *,
        symbol: str,
        channel: AlertChannel,
        level: AlertLevel,
        delivery_status: AlertDeliveryStatus,
        title: str,
        message: str,
        error_detail: str,
    ) -> EventRecordRead:
        return self.event_service.record_event(
            db,
            event_type="notification.delivery",
            source="notification",
            severity=level.value,
            title=title,
            message=message,
            symbol=symbol,
            status=delivery_status.value,
            entity_type="notification",
            payload={
                "channel": channel.value,
                "delivery_status": delivery_status.value,
                "error_detail": error_detail,
            },
        )

    def _now(self):
        from datetime import UTC, datetime

        return datetime.now(UTC)
