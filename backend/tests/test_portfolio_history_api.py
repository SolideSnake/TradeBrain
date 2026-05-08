from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.adapters.persistence.sqlite.db import get_session_factory
from app.application.portfolio_history_service import PortfolioHistoryService
from app.domains.portfolio_history.models import PortfolioHistoryPoint


def test_snapshot_success_records_portfolio_history_point(client):
    snapshot_response = client.get("/api/snapshot")
    assert snapshot_response.status_code == 200

    response = client.get("/api/portfolio/history?range=1D")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["account_id"] == "TEST-ACCOUNT"
    assert payload[0]["broker_profile"] == "paper"
    assert payload[0]["currency"] == "USD"
    assert payload[0]["net_liquidation"] == 250000.0
    assert payload[0]["cash_balance"] == 82000.0
    assert payload[0]["available_funds"] == 82000.0
    assert payload[0]["buying_power"] == 164000.0


def test_snapshot_failure_does_not_record_portfolio_history(client, monkeypatch):
    from app.api import router as router_module

    assert client.get("/api/snapshot").status_code == 200
    before = client.get("/api/portfolio/history?range=1D").json()

    class FailingSnapshotBuilder:
        def build(self, db):
            raise RuntimeError("IBKR timeout")

    monkeypatch.setattr(
        router_module.snapshot_cache_service,
        "snapshot_builder",
        FailingSnapshotBuilder(),
    )

    response = client.post("/api/snapshot/refresh")
    assert response.status_code == 200

    after = client.get("/api/portfolio/history?range=1D").json()
    assert len(after) == len(before)


def test_portfolio_history_endpoint_returns_time_ascending_and_samples(client):
    now = datetime.now(timezone.utc)
    with get_session_factory()() as db:
        for index in range(505):
            db.add(
                PortfolioHistoryPoint(
                    recorded_at=now - timedelta(minutes=504 - index),
                    account_id="TEST-ACCOUNT",
                    broker_profile="paper",
                    currency="USD",
                    net_liquidation=float(index),
                    cash_balance=1000.0,
                    available_funds=900.0,
                    buying_power=1800.0,
                    unrealized_pnl=10.0,
                    positions_market_value=500.0,
                    source_snapshot_at=now - timedelta(minutes=504 - index),
                )
            )
        db.commit()

    response = client.get("/api/portfolio/history?range=1D")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) <= 500
    assert payload[0]["net_liquidation"] == 0.0
    assert payload[-1]["net_liquidation"] == 504.0
    recorded_times = [point["recorded_at"] for point in payload]
    assert recorded_times == sorted(recorded_times)


def test_portfolio_history_service_prunes_old_and_overflow_rows(client):
    now = datetime.now(timezone.utc)
    service = PortfolioHistoryService(retention_days=365, max_rows=2)

    with get_session_factory()() as db:
        db.add_all(
            [
                PortfolioHistoryPoint(
                    recorded_at=now - timedelta(days=366),
                    account_id="TEST-ACCOUNT",
                    broker_profile="paper",
                    currency="USD",
                    net_liquidation=1.0,
                ),
                PortfolioHistoryPoint(
                    recorded_at=now - timedelta(minutes=2),
                    account_id="TEST-ACCOUNT",
                    broker_profile="paper",
                    currency="USD",
                    net_liquidation=2.0,
                ),
                PortfolioHistoryPoint(
                    recorded_at=now - timedelta(minutes=1),
                    account_id="TEST-ACCOUNT",
                    broker_profile="paper",
                    currency="USD",
                    net_liquidation=3.0,
                ),
                PortfolioHistoryPoint(
                    recorded_at=now,
                    account_id="TEST-ACCOUNT",
                    broker_profile="paper",
                    currency="USD",
                    net_liquidation=4.0,
                ),
            ]
        )
        db.commit()

        service.repository.prune(db, retention_days=service.retention_days, max_rows=service.max_rows, now=now)
        db.commit()

        records = service.repository.list_since(
            db,
            since=now - timedelta(days=400),
            broker_profile="paper",
        )

    assert [record.net_liquidation for record in records] == [3.0, 4.0]
