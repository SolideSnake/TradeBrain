from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.adapters.persistence.sqlite.db import get_session_factory
from app.adapters.persistence.sqlite.snapshot_repository import SnapshotRepository
from app.jobs.snapshot_refresh_job import SnapshotRefreshJob


def test_snapshot_refresh_settings_default_to_five_minutes_enabled(client):
    response = client.get("/api/settings/snapshot-refresh")

    assert response.status_code == 200
    assert response.json() == {
        "enabled": True,
        "interval_seconds": 300,
    }


def test_snapshot_refresh_settings_can_be_updated(client):
    response = client.put(
        "/api/settings/snapshot-refresh",
        json={
            "enabled": False,
            "interval_seconds": 300,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "enabled": False,
        "interval_seconds": 300,
    }

    follow_up = client.get("/api/settings/snapshot-refresh")
    assert follow_up.status_code == 200
    assert follow_up.json()["enabled"] is False
    assert follow_up.json()["interval_seconds"] == 300


def test_snapshot_refresh_settings_reject_invalid_interval(client):
    response = client.put(
        "/api/settings/snapshot-refresh",
        json={
            "enabled": True,
            "interval_seconds": 60,
        },
    )

    assert response.status_code == 422


def test_snapshot_refresh_job_runs_when_due(client):
    class FakeSnapshotCacheService:
        def __init__(self) -> None:
            self.calls = 0

        def refresh(self, db, trigger="manual"):
            self.calls += 1

    fake_service = FakeSnapshotCacheService()
    now = datetime.now(timezone.utc)
    job = SnapshotRefreshJob(
        session_factory=get_session_factory(),
        snapshot_cache_service=fake_service,
        started_at=now - timedelta(seconds=301),
    )

    did_refresh = job.run_once(now=now)

    assert did_refresh is True
    assert fake_service.calls == 1


def test_snapshot_refresh_job_records_automatic_refresh_event(client):
    client.post("/api/watchlist", json={"symbol": "AAPL"})

    now = datetime.now(timezone.utc)
    job = SnapshotRefreshJob(
        session_factory=get_session_factory(),
        started_at=now - timedelta(seconds=301),
    )

    did_refresh = job.run_once(now=now)

    assert did_refresh is True
    response = client.get("/api/events")
    assert response.status_code == 200
    event = response.json()[0]
    assert event["event_type"] == "snapshot.refresh"
    assert event["status"] == "success"
    assert event["payload"]["trigger"] == "automatic"


def test_snapshot_refresh_job_does_not_run_when_disabled(client):
    client.put(
        "/api/settings/snapshot-refresh",
        json={
            "enabled": False,
            "interval_seconds": 300,
        },
    )

    class FakeSnapshotCacheService:
        def __init__(self) -> None:
            self.calls = 0

        def refresh(self, db, trigger="manual"):
            self.calls += 1

    fake_service = FakeSnapshotCacheService()
    now = datetime.now(timezone.utc)
    job = SnapshotRefreshJob(
        session_factory=get_session_factory(),
        snapshot_cache_service=fake_service,
        started_at=now - timedelta(seconds=301),
    )

    did_refresh = job.run_once(now=now)

    assert did_refresh is False
    assert fake_service.calls == 0


def test_snapshot_refresh_job_skips_active_refresh(client):
    class FakeSnapshotCacheService:
        def __init__(self) -> None:
            self.calls = 0

        def refresh(self, db, trigger="manual"):
            self.calls += 1

    now = datetime.now(timezone.utc)
    with get_session_factory()() as db:
        SnapshotRepository().mark_refreshing(db)
        db.commit()

    fake_service = FakeSnapshotCacheService()
    job = SnapshotRefreshJob(
        session_factory=get_session_factory(),
        snapshot_cache_service=fake_service,
        started_at=now - timedelta(seconds=301),
    )

    did_refresh = job.run_once(now=now)

    assert did_refresh is False
    assert fake_service.calls == 0
