from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.database.client import create_client
from app.database.indexes import ensure_indexes
from app.errors import register_error_handlers
from app.routes import auth, events, health, users


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the app. Run it with `uvicorn app.main:create_app --factory`."""
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        client = create_client(settings.mongodb_url, settings.mongodb_timeout_ms)
        app.state.mongo_client = client
        app.state.db = client[settings.database_name]
        try:
            # Fails fast when MongoDB is unreachable, so a broken deploy does not start.
            await ensure_indexes(app.state.db)
            yield
        finally:
            await client.close()

    app = FastAPI(title="Seatwise API", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(events.router)
    return app
