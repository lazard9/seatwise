from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.config import get_settings
from app.database.client import create_client
from app.database.indexes import ensure_indexes


@asynccontextmanager
async def open_database() -> AsyncIterator[AsyncDatabase[dict[str, Any]]]:
    """The database from `backend/.env`, with every index in place, like the app at startup."""
    settings = get_settings()
    client = create_client(settings.mongodb_url, settings.mongodb_timeout_ms)
    try:
        db = client[settings.database_name]
        await ensure_indexes(db)
        yield db
    finally:
        await client.close()
