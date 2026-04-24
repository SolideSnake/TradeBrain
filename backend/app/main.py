from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.adapters.persistence.sqlite.db import init_db
from app.api.router import router
from app.config.settings import get_settings
from app.jobs.snapshot_refresh_job import SnapshotRefreshJob
from app.observability.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    init_db()
    settings = get_settings()
    refresh_job = None
    if settings.app_env != "test":
        refresh_job = SnapshotRefreshJob()
        refresh_job.start()
        app.state.snapshot_refresh_job = refresh_job
    yield
    if refresh_job is not None:
        await refresh_job.stop()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.include_router(router)
    return app


app = create_app()

