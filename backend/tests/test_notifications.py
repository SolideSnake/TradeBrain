from datetime import UTC, datetime

from app.adapters.persistence.sqlite.alert_rule_repository import AlertRuleRepository
from app.adapters.persistence.sqlite.db import get_session_factory
from app.application.notifications import NotificationService
from app.core.types.common import (
    AlertDeliveryStatus,
    AlertRuleMetric,
    AlertRuleOperator,
    AlertRuleSource,
)
from app.domains.alerting.models import AlertRule
from app.domains.alerting.rules import AlertRuleEngine
from app.domains.alerting.schemas import AlertRuleCreate
from app.domains.indicators.schemas import IndicatorSnapshot
from app.domains.portfolio.schemas import AccountSnapshot
from app.domains.snapshot.schemas import (
    CanonicalSnapshot,
    CanonicalWatchlistItem,
    SnapshotMeta,
    SnapshotSummary,
)


class FakeNotifier:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.messages: list[str] = []

    def send_message(self, text: str):
        self.messages.append(text)
        if self.should_fail:
            raise RuntimeError("telegram offline")
        return type("Result", (), {"status": "sent", "external_id": "42"})()


def build_snapshot(drawdown: float = 6.5) -> CanonicalSnapshot:
    now = datetime.now(UTC)
    return CanonicalSnapshot(
        meta=SnapshotMeta(
            generated_at=now,
            broker_mode="mock",
            broker_status="mock",
        ),
        summary=SnapshotSummary(
            tracked_symbols=1,
            enabled_symbols=1,
            symbols_in_position=0,
            quote_coverage=1,
            position_count=0,
        ),
        account=AccountSnapshot(
            account_id="MOCK",
            net_liquidation=250000.0,
            available_funds=82000.0,
            buying_power=164000.0,
            source="mock",
            updated_at=now,
        ),
        watchlist=[
            CanonicalWatchlistItem(
                id=1,
                symbol="NVDA",
                name="NVIDIA Corporation",
                market="US",
                asset_type="stock",
                group_name="default",
                enabled=True,
                in_position=False,
                notes="",
                indicators=IndicatorSnapshot(
                    current_price=202.06,
                    day_change_percent=0.0,
                    drawdown_from_52w_high_percent=drawdown,
                ),
            )
        ],
        positions=[],
    )


def test_alert_rule_engine_generates_watchlist_candidate():
    rule_engine = AlertRuleEngine()
    rule = AlertRule(
        id=1,
        name="NVDA 52W 回撤提醒",
        enabled=True,
        source=AlertRuleSource.WATCHLIST,
        symbol="NVDA",
        metric=AlertRuleMetric.DRAWDOWN_52W,
        operator=AlertRuleOperator.ABOVE,
        threshold_value="5",
    )

    evaluations = rule_engine.evaluate_snapshot(build_snapshot(), [rule])

    assert len(evaluations) == 1
    assert evaluations[0].rule_id == 1
    assert evaluations[0].matched is True
    assert evaluations[0].should_notify is True
    assert evaluations[0].candidate is not None
    assert evaluations[0].candidate.symbol == "NVDA"
    assert "52W 回撤 高于 5" in evaluations[0].candidate.message
    assert "当前值: 6.50%" in evaluations[0].candidate.message


def test_alert_rule_engine_suppresses_already_matched_edge_rule():
    rule_engine = AlertRuleEngine()
    rule = AlertRule(
        id=1,
        name="NVDA 52W 回撤提醒",
        enabled=True,
        source=AlertRuleSource.WATCHLIST,
        symbol="NVDA",
        metric=AlertRuleMetric.DRAWDOWN_52W,
        operator=AlertRuleOperator.ABOVE,
        threshold_value="5",
        last_matched=True,
    )

    evaluations = rule_engine.evaluate_snapshot(build_snapshot(), [rule])

    assert evaluations[0].matched is True
    assert evaluations[0].should_notify is False
    assert evaluations[0].suppression_reason == "condition_already_matched"
    assert evaluations[0].candidate is None


def test_alert_rule_engine_cross_above_uses_previous_value():
    rule_engine = AlertRuleEngine()
    rule = AlertRule(
        id=1,
        name="NVDA 上穿 52W 回撤提醒",
        enabled=True,
        source=AlertRuleSource.WATCHLIST,
        symbol="NVDA",
        metric=AlertRuleMetric.DRAWDOWN_52W,
        operator=AlertRuleOperator.CROSS_ABOVE,
        threshold_value="5",
        last_observed_value="4.5",
    )

    evaluations = rule_engine.evaluate_snapshot(build_snapshot(drawdown=6.5), [rule])

    assert evaluations[0].matched is True
    assert evaluations[0].should_notify is True


def test_notification_service_sends_and_updates_rule_counters(client):
    notifier = FakeNotifier()
    alert_rule_repository = AlertRuleRepository()
    service = NotificationService(
        alert_rule_repository=alert_rule_repository,
        notifier=notifier,
    )
    session = get_session_factory()()

    try:
        rule = alert_rule_repository.create(
            session,
            AlertRuleCreate(
                name="NVDA 52W 回撤提醒",
                source=AlertRuleSource.WATCHLIST,
                symbol="NVDA",
                metric=AlertRuleMetric.DRAWDOWN_52W,
                operator=AlertRuleOperator.ABOVE,
                threshold_value="5",
            ),
        )

        events = service.handle_snapshot(session, build_snapshot())
        session.refresh(rule)
        recent = service.event_service.list_recent(session)
    finally:
        session.close()

    assert len(notifier.messages) == 1
    assert len(events) == 1
    assert events[0].status == AlertDeliveryStatus.SENT
    assert rule.sent_count == 1
    assert rule.failed_count == 0
    assert rule.last_matched is True
    assert rule.last_observed_value == "6.5"
    assert recent[0].symbol == "NVDA"


def test_notification_service_can_send_rule_to_feishu(client):
    notifier = FakeNotifier()
    alert_rule_repository = AlertRuleRepository()
    service = NotificationService(
        alert_rule_repository=alert_rule_repository,
        feishu_notifier=notifier,
    )
    session = get_session_factory()()

    try:
        rule = alert_rule_repository.create(
            session,
            AlertRuleCreate(
                name="NVDA 52W 回撤提醒",
                source=AlertRuleSource.WATCHLIST,
                symbol="NVDA",
                metric=AlertRuleMetric.DRAWDOWN_52W,
                operator=AlertRuleOperator.ABOVE,
                threshold_value="5",
            ),
        )

        events = service.handle_snapshot(session, build_snapshot())
        session.refresh(rule)
    finally:
        session.close()

    assert len(notifier.messages) == 1
    assert len(events) == 1
    assert events[0].payload["channel"] == "feishu"
    assert events[0].status == AlertDeliveryStatus.SENT
    assert rule.sent_count == 1
    assert rule.failed_count == 0


def test_notification_service_suppresses_repeated_edge_rule(client):
    notifier = FakeNotifier()
    alert_rule_repository = AlertRuleRepository()
    service = NotificationService(
        alert_rule_repository=alert_rule_repository,
        notifier=notifier,
    )
    session = get_session_factory()()

    try:
        rule = alert_rule_repository.create(
            session,
            AlertRuleCreate(
                name="NVDA 52W 回撤提醒",
                source=AlertRuleSource.WATCHLIST,
                symbol="NVDA",
                metric=AlertRuleMetric.DRAWDOWN_52W,
                operator=AlertRuleOperator.ABOVE,
                threshold_value="5",
            ),
        )

        first_events = service.handle_snapshot(session, build_snapshot())
        second_events = service.handle_snapshot(session, build_snapshot())
        session.refresh(rule)
    finally:
        session.close()

    assert len(first_events) == 1
    assert len(second_events) == 0
    assert len(notifier.messages) == 1
    assert rule.sent_count == 1
    assert rule.suppressed_count == 1


def test_notification_service_records_failed_rule_delivery(client):
    notifier = FakeNotifier(should_fail=True)
    alert_rule_repository = AlertRuleRepository()
    service = NotificationService(
        alert_rule_repository=alert_rule_repository,
        notifier=notifier,
    )
    session = get_session_factory()()

    try:
        rule = alert_rule_repository.create(
            session,
            AlertRuleCreate(
                name="账户净值提醒",
                source=AlertRuleSource.PORTFOLIO,
                metric=AlertRuleMetric.NET_LIQUIDATION,
                operator=AlertRuleOperator.ABOVE,
                threshold_value="200000",
            ),
        )

        events = service.handle_snapshot(session, build_snapshot())
        session.refresh(rule)
    finally:
        session.close()

    assert len(events) == 1
    assert events[0].status == AlertDeliveryStatus.FAILED
    assert rule.sent_count == 0
    assert rule.failed_count == 1
    assert "telegram offline" in rule.last_error


def test_notification_service_can_send_test_notification_and_log_event(client):
    notifier = FakeNotifier()
    service = NotificationService(notifier=notifier)
    session = get_session_factory()()

    try:
        settings_service = service.notification_settings_service
        settings = settings_service.repository.get(session)
        if settings is None:
            from app.domains.preferences.models import NotificationSettings

            settings = NotificationSettings(
                telegram_bot_token="123456:ABCDEF-secret",
                telegram_chat_id="99887766",
            )
        else:
            settings.telegram_bot_token = "123456:ABCDEF-secret"
            settings.telegram_chat_id = "99887766"
        settings_service.repository.save(session, settings)
        session.commit()

        result = service.send_test_notification(session)
        recent = service.event_service.list_recent(session)
    finally:
        session.close()

    assert result.success is True
    assert result.delivery_status == AlertDeliveryStatus.SENT
    assert len(notifier.messages) == 1
    assert recent[0].symbol == "SYSTEM"
    assert recent[0].title == "Telegram 测试消息"
