from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.database.client import create_client
from app.routes import health


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the app. Run it with `uvicorn app.main:create_app --factory`."""
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        client = create_client(settings.mongodb_url, settings.mongodb_timeout_ms)
        app.state.mongo_client = client
        app.state.db = client[settings.database_name]
        try:
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

    app.include_router(health.router)
    return app
