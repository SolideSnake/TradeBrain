from __future__ import annotations

from sqlalchemy.orm import Session

from app.adapters.persistence.sqlite.alert_repository import AlertRepository
from app.adapters.telegram.client import TelegramNotifier, create_telegram_notifier
from app.application.notification_settings_service import NotificationSettingsService
from app.core.types.common import AlertChannel, AlertDeliveryStatus, AlertLevel, ValuationLabel
from app.domains.alerts.schemas import AlertEventRead
from app.domains.indicators.schemas import IndicatorSnapshot
from app.domains.state.schemas import WatchlistStateSnapshot


class AlertRouter:
    def __init__(
        self,
        alert_repository: AlertRepository | None = None,
        notifier: TelegramNotifier | None = None,
        notification_settings_service: NotificationSettingsService | None = None,
    ) -> None:
        self.alert_repository = alert_repository or AlertRepository()
        self.notifier = notifier
        self.notification_settings_service = notification_settings_service or NotificationSettingsService()

    def route_state_changes(
        self,
        db: Session,
        states_by_symbol: dict[str, WatchlistStateSnapshot],
        indicators_by_symbol: dict[str, IndicatorSnapshot | None],
    ) -> list[AlertEventRead]:
        events = []

        for symbol, state in states_by_symbol.items():
            if not state.has_changed or state.current_label is None or state.previous_label is None:
                continue

            indicator = indicators_by_symbol.get(symbol)
            title = f"{symbol} 估值状态变化"
            message = self._build_state_change_message(symbol, state, indicator)
            error_detail = ""
            notifier = self.notifier or self._resolve_notifier(db)

            try:
                result = notifier.send_message(message)
                delivery_status = AlertDeliveryStatus(result.status)
            except Exception as exc:
                delivery_status = AlertDeliveryStatus.FAILED
                error_detail = str(exc)

            event = self.alert_repository.create(
                db,
                symbol=symbol,
                channel=AlertChannel.TELEGRAM,
                level=AlertLevel.INFO,
                delivery_status=delivery_status,
                title=title,
                message=message,
                error_detail=error_detail,
            )
            db.flush()
            db.refresh(event)
            events.append(AlertEventRead.model_validate(event, from_attributes=True))

        if events:
            db.commit()

        return events

    def list_recent(self, db: Session, limit: int = 50) -> list[AlertEventRead]:
        return [
            AlertEventRead.model_validate(event, from_attributes=True)
            for event in self.alert_repository.list_recent(db, limit)
        ]

    def _build_state_change_message(
        self,
        symbol: str,
        state: WatchlistStateSnapshot,
        indicator: IndicatorSnapshot | None,
    ) -> str:
        lines = [
            f"{symbol} 估值状态变化",
            f"状态: {self._label_text(state.previous_label)} -> {self._label_text(state.current_label)}",
        ]

        if indicator and indicator.peg_ratio is not None:
            lines.append(f"PEG: {indicator.peg_ratio:.2f}")
        if indicator and indicator.pe_ratio is not None:
            lines.append(f"PE: {indicator.pe_ratio:.2f}")
        if indicator and indicator.earnings_growth_rate_percent is not None:
            lines.append(f"增长率: {indicator.earnings_growth_rate_percent:.2f}%")
        lines.append(f"时间: {state.evaluated_at.isoformat()}")
        return "\n".join(lines)

    def _label_text(self, label: ValuationLabel | None) -> str:
        mapping = {
            ValuationLabel.UNDERVALUED: "低估",
            ValuationLabel.FAIR: "合理",
            ValuationLabel.OVERVALUED: "高估",
        }
        return mapping.get(label, "--")

    def _resolve_notifier(self, db: Session) -> TelegramNotifier:
        bot_token, chat_id = self.notification_settings_service.resolve_telegram_credentials(db)
        return create_telegram_notifier(bot_token, chat_id)
