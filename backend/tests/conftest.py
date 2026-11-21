import os
from collections.abc import AsyncIterator
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pymongo.asynchronous.database import AsyncDatabase

from app.config import Settings
from app.main import create_app

TEST_DATABASE = "seatwise_test"
TEST_SECRET = "test-secret-that-is-long-enough-for-hs256-signing"
DEFAULT_TEST_MONGODB_URL = "mongodb://localhost:27017/?replicaSet=rs0"


def make_settings(**overrides: Any) -> Settings:
    """Settings for tests. Never reads `.env`, never touches the dev database."""
    values: dict[str, Any] = {
        "mongodb_url": os.environ.get("MONGODB_URL", DEFAULT_TEST_MONGODB_URL),
        "database_name": TEST_DATABASE,
        "jwt_secret": TEST_SECRET,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


@pytest.fixture(scope="session")
def settings() -> Settings:
    return make_settings()


@pytest.fixture(scope="session")
async def app(settings: Settings) -> AsyncIterator[FastAPI]:
    application = create_app(settings)
    async with application.router.lifespan_context(application):
        await application.state.mongo_client.drop_database(TEST_DATABASE)
        yield application
        await application.state.mongo_client.drop_database(TEST_DATABASE)


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def db(app: FastAPI) -> AsyncDatabase[dict[str, Any]]:
    return app.state.db
