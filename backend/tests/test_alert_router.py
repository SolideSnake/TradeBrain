from datetime import UTC, datetime

from app.adapters.persistence.sqlite.alert_repository import AlertRepository
from app.adapters.persistence.sqlite.db import get_session_factory
from app.application.alert_router import AlertRouter
from app.core.types.common import AlertDeliveryStatus, ValuationLabel
from app.domains.indicators.schemas import IndicatorSnapshot
from app.domains.state.schemas import WatchlistStateSnapshot


class FakeNotifier:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def send_message(self, text: str):
        self.messages.append(text)
        return type("Result", (), {"status": "sent", "external_id": "42"})()


def test_alert_router_sends_and_persists_state_change(client):
    notifier = FakeNotifier()
    router = AlertRouter(alert_repository=AlertRepository(), notifier=notifier)
    session = get_session_factory()()

    try:
        states_by_symbol = {
            "AAPL": WatchlistStateSnapshot(
                symbol="AAPL",
                current_label=ValuationLabel.UNDERVALUED,
                previous_label=ValuationLabel.FAIR,
                has_changed=True,
                changed_at=datetime.now(UTC),
                evaluated_at=datetime.now(UTC),
            )
        }
        indicators_by_symbol = {
            "AAPL": IndicatorSnapshot(
                peg_ratio=0.72,
                pe_ratio=18.4,
                earnings_growth_rate_percent=25.6,
            )
        }

        events = router.route_state_changes(session, states_by_symbol, indicators_by_symbol)
        recent = router.list_recent(session)
    finally:
        session.close()

    assert len(notifier.messages) == 1
    assert len(events) == 1
    assert events[0].delivery_status == AlertDeliveryStatus.SENT
    assert events[0].symbol == "AAPL"
    assert "合理 -> 低估" in notifier.messages[0]
    assert recent[0].symbol == "AAPL"
