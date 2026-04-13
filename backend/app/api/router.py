from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlite.db import get_db
from app.application.snapshot_builder import SnapshotBuilder
from app.application.watchlist_service import WatchlistService
from app.config.settings import get_settings
from app.domains.watchlist.errors import DuplicateWatchlistSymbolError
from app.domains.snapshot.schemas import CanonicalSnapshot
from app.domains.watchlist.schemas import (
    WatchlistEntryCreate,
    WatchlistEntryRead,
    WatchlistEntryUpdate,
)

router = APIRouter()
watchlist_service = WatchlistService()


@router.get("/api/health")
def healthcheck() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "environment": settings.app_env}


@router.get("/api/watchlist", response_model=list[WatchlistEntryRead])
def list_watchlist(db: Session = Depends(get_db)) -> list[WatchlistEntryRead]:
    return watchlist_service.list_entries(db)


@router.get("/api/snapshot", response_model=CanonicalSnapshot)
def get_snapshot(db: Session = Depends(get_db)) -> CanonicalSnapshot:
    return SnapshotBuilder().build(db)


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
