from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.adapters.persistence.sqlite.db import get_session_factory
from app.application.event_service import EventService


def test_events_endpoint_returns_recent_events(client):
    with get_session_factory()() as db:
        EventService().record_event(
            db,
            event_type="snapshot.refresh",
            source="snapshot",
            status="success",
            title="快照刷新成功",
            message="测试事件",
        )
        db.commit()

    response = client.get("/api/events")

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["event_type"] == "snapshot.refresh"
    assert payload[0]["source"] == "snapshot"
    assert payload[0]["status"] == "success"


def test_event_service_prunes_old_and_overflow_events(client):
    now = datetime.now(timezone.utc)
    service = EventService(retention_days=90, max_rows=2)

    with get_session_factory()() as db:
        service.record_event(
            db,
            event_type="test.old",
            source="test",
            title="旧事件",
            occurred_at=now - timedelta(days=91),
        )
        service.record_event(
            db,
            event_type="test.first",
            source="test",
            title="第一条",
            occurred_at=now - timedelta(minutes=2),
        )
        service.record_event(
            db,
            event_type="test.second",
            source="test",
            title="第二条",
            occurred_at=now - timedelta(minutes=1),
        )
        service.record_event(
            db,
            event_type="test.third",
            source="test",
            title="第三条",
            occurred_at=now,
        )
        db.commit()

        events = service.list_recent(db, limit=10)

    assert [event.event_type for event in events] == ["test.third", "test.second"]
