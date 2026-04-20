from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlite.db import get_db
from app.application.alert_router import AlertRouter
from app.application.ibkr_settings_service import IBKRSettingsService
from app.application.notification_settings_service import NotificationSettingsService
from app.application.snapshot_cache_service import SnapshotCacheService
from app.application.state_engine import StateEngine
from app.application.watchlist_service import WatchlistService
from app.config.settings import get_settings
from app.domains.alerts.schemas import AlertEventRead
from app.domains.preferences.schemas import (
    IBKRConnectionTestRequest,
    IBKRConnectionTestResult,
    IBKRSettingsRead,
    IBKRSettingsUpdate,
    NotificationSettingsRead,
    NotificationSettingsUpdate,
    NotificationTestResult,
)
from app.domains.snapshot.schemas import SnapshotResponse
from app.domains.state.schemas import WatchlistStateSnapshot
from app.domains.watchlist.errors import DuplicateWatchlistSymbolError
from app.domains.watchlist.schemas import (
    WatchlistEntryCreate,
    WatchlistEntryRead,
    WatchlistEntryUpdate,
)

router = APIRouter()
watchlist_service = WatchlistService()
state_engine = StateEngine()
alert_router = AlertRouter()
notification_settings_service = NotificationSettingsService()
ibkr_settings_service = IBKRSettingsService()
snapshot_cache_service = SnapshotCacheService()


@router.get("/api/health")
def healthcheck() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "environment": settings.app_env}


@router.get("/api/watchlist", response_model=list[WatchlistEntryRead])
def list_watchlist(db: Session = Depends(get_db)) -> list[WatchlistEntryRead]:
    return watchlist_service.list_entries(db)


@router.get("/api/snapshot", response_model=SnapshotResponse)
def get_snapshot(db: Session = Depends(get_db)) -> SnapshotResponse:
    return snapshot_cache_service.get_latest(db)


@router.post("/api/snapshot/refresh", response_model=SnapshotResponse)
def refresh_snapshot(db: Session = Depends(get_db)) -> SnapshotResponse:
    return snapshot_cache_service.refresh(db)


@router.get("/api/states", response_model=list[WatchlistStateSnapshot])
def list_states(db: Session = Depends(get_db)) -> list[WatchlistStateSnapshot]:
    return state_engine.list_states(db)


@router.get("/api/alerts", response_model=list[AlertEventRead])
def list_alerts(db: Session = Depends(get_db)) -> list[AlertEventRead]:
    return alert_router.list_recent(db)


@router.get("/api/settings/notifications", response_model=NotificationSettingsRead)
def get_notification_settings(db: Session = Depends(get_db)) -> NotificationSettingsRead:
    return notification_settings_service.get_settings(db)


@router.put("/api/settings/notifications", response_model=NotificationSettingsRead)
def update_notification_settings(
    payload: NotificationSettingsUpdate,
    db: Session = Depends(get_db),
) -> NotificationSettingsRead:
    return notification_settings_service.update_settings(db, payload)


@router.post("/api/settings/notifications/test", response_model=NotificationTestResult)
def test_notification_settings(db: Session = Depends(get_db)) -> NotificationTestResult:
    return notification_settings_service.send_test_message(db)


@router.get("/api/settings/ibkr", response_model=IBKRSettingsRead)
def get_ibkr_settings(db: Session = Depends(get_db)) -> IBKRSettingsRead:
    return ibkr_settings_service.get_settings(db)


@router.put("/api/settings/ibkr", response_model=IBKRSettingsRead)
def update_ibkr_settings(
    payload: IBKRSettingsUpdate,
    db: Session = Depends(get_db),
) -> IBKRSettingsRead:
    return ibkr_settings_service.update_settings(db, payload)


@router.post("/api/settings/ibkr/test", response_model=IBKRConnectionTestResult)
def test_ibkr_settings(
    payload: IBKRConnectionTestRequest,
    db: Session = Depends(get_db),
) -> IBKRConnectionTestResult:
    return ibkr_settings_service.test_connection(db, payload)


@router.post(
    "/api/watchlist",
    response_model=WatchlistEntryRead,
    status_code=status.HTTP_201_CREATED,
)
def create_watchlist_entry(
    payload: WatchlistEntryCreate, db: Session = Depends(get_db)
) -> WatchlistEntryRead:
    try:
        return watchlist_service.create_entry(db, payload)
    except DuplicateWatchlistSymbolError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Watchlist already contains symbol '{exc}'.",
        ) from exc


@router.patch("/api/watchlist/{entry_id}", response_model=WatchlistEntryRead)
def update_watchlist_entry(
    entry_id: int,
    payload: WatchlistEntryUpdate,
    db: Session = Depends(get_db),
) -> WatchlistEntryRead:
    entry = watchlist_service.update_entry(db, entry_id, payload)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    return entry


@router.delete("/api/watchlist/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watchlist_entry(entry_id: int, db: Session = Depends(get_db)) -> Response:
    deleted = watchlist_service.delete_entry(db, entry_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
