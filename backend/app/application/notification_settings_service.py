from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session

from app.adapters.persistence.sqlite.alert_repository import AlertRepository
from app.adapters.persistence.sqlite.notification_settings_repository import (
    NotificationSettingsRepository,
)
from app.adapters.telegram.client import (
    TelegramNotifier,
    create_telegram_notifier,
)
from app.config.settings import Settings, get_settings
from app.core.types.common import AlertChannel, AlertDeliveryStatus, AlertLevel
from app.domains.alerts.schemas import AlertEventRead
from app.domains.preferences.models import NotificationSettings
from app.domains.preferences.schemas import (
    NotificationSettingsRead,
    NotificationSettingsUpdate,
    NotificationTestResult,
)


class NotificationSettingsService:
    def __init__(
        self,
        repository: NotificationSettingsRepository | None = None,
        settings: Settings | None = None,
        alert_repository: AlertRepository | None = None,
        notifier_factory: Callable[[str, str], TelegramNotifier] | None = None,
    ) -> None:
        self.repository = repository or NotificationSettingsRepository()
        self.settings = settings or get_settings()
        self.alert_repository = alert_repository or AlertRepository()
        self.notifier_factory = notifier_factory or create_telegram_notifier

    def get_settings(self, db: Session) -> NotificationSettingsRead:
        stored = self.repository.get(db)
        stored_token = stored.telegram_bot_token if stored else ""
        stored_chat_id = stored.telegram_chat_id if stored else ""

        token = stored_token or self.settings.telegram_bot_token
        chat_id = stored_chat_id or self.settings.telegram_chat_id

        if stored_token or stored_chat_id:
            source = "database"
        elif token or chat_id:
            source = "environment"
        else:
            source = "none"

        return NotificationSettingsRead(
            telegram_enabled=bool(token and chat_id),
            telegram_bot_token_configured=bool(token),
            telegram_bot_token_masked=self._mask_token(token) if token else None,
            telegram_chat_id=chat_id or "",
            source=source,
        )

    def update_settings(
        self,
        db: Session,
        payload: NotificationSettingsUpdate,
    ) -> NotificationSettingsRead:
        stored = self.repository.get(db)
        if stored is None:
            stored = NotificationSettings()

        updates = payload.model_dump(exclude_unset=True)
        if "telegram_bot_token" in updates:
            stored.telegram_bot_token = updates["telegram_bot_token"] or ""
        if "telegram_chat_id" in updates:
            stored.telegram_chat_id = updates["telegram_chat_id"] or ""

        self.repository.save(db, stored)
        db.commit()
        db.refresh(stored)

        return self.get_settings(db)

    def resolve_telegram_credentials(self, db: Session) -> tuple[str, str]:
        stored = self.repository.get(db)
        stored_token = stored.telegram_bot_token if stored else ""
        stored_chat_id = stored.telegram_chat_id if stored else ""

        token = stored_token or self.settings.telegram_bot_token
        chat_id = stored_chat_id or self.settings.telegram_chat_id
        return token, chat_id

    def send_test_message(self, db: Session) -> NotificationTestResult:
        bot_token, chat_id = self.resolve_telegram_credentials(db)
        if not bot_token or not chat_id:
            self._record_alert(
                db,
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

        notifier = self.notifier_factory(bot_token, chat_id)
        message = "TradeBrain Telegram 测试消息\n如果你收到这条消息，说明当前保存的 Telegram 配置可用。"

        try:
            notifier.send_message(message)
            delivery_status = AlertDeliveryStatus.SENT
            detail = "测试消息已发送。请检查 Telegram。"
            error_detail = ""
        except Exception as exc:
            delivery_status = AlertDeliveryStatus.FAILED
            detail = "测试消息发送失败。"
            error_detail = str(exc)

        self._record_alert(
            db,
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

    def _record_alert(
        self,
        db: Session,
        delivery_status: AlertDeliveryStatus,
        title: str,
        message: str,
        error_detail: str,
    ) -> AlertEventRead:
        event = self.alert_repository.create(
            db,
            symbol="SYSTEM",
            channel=AlertChannel.TELEGRAM,
            level=AlertLevel.INFO,
            delivery_status=delivery_status,
            title=title,
            message=message,
            error_detail=error_detail,
        )
        db.flush()
        db.refresh(event)
        return AlertEventRead.model_validate(event, from_attributes=True)

    def _mask_token(self, token: str) -> str:
        if len(token) <= 10:
            return "*" * len(token)
        return f"{token[:6]}...{token[-4:]}"
