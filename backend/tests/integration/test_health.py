from typing import Any

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import ServerSelectionTimeoutError

from app.database.client import create_client
from app.main import create_app
from tests.conftest import TEST_DATABASE, make_settings

UNREACHABLE_URL = "mongodb://127.0.0.1:1/"  # nothing listens on port 1


async def test_health_reports_ok_when_database_is_reachable(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


async def test_health_returns_503_when_database_goes_away(
    app: FastAPI, client: AsyncClient
) -> None:
    unreachable = create_client(UNREACHABLE_URL, timeout_ms=200)
    original_db = app.state.db
    app.state.db = unreachable[TEST_DATABASE]
    try:
        response = await client.get("/health")
    finally:
        app.state.db = original_db
        await unreachable.close()

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "unavailable"}


async def test_startup_fails_when_database_is_unreachable() -> None:
    app = create_app(make_settings(mongodb_url=UNREACHABLE_URL, mongodb_timeout_ms=200))

    with pytest.raises(ServerSelectionTimeoutError):
        async with app.router.lifespan_context(app):
            pass


async def test_tests_run_against_a_replica_set(db: AsyncDatabase[dict[str, Any]]) -> None:
    # Transactions need a replica set; fail loudly if tests run against a standalone server.
    hello = await db.command("hello")

    assert hello.get("setName"), "MongoDB is not running as a replica set"
    assert db.name == TEST_DATABASE


async def test_transactions_work_on_the_test_database(
    db: AsyncDatabase[dict[str, Any]],
) -> None:
    collection = db["transaction_check"]

    async with db.client.start_session() as session, await session.start_transaction():
        await collection.insert_one({"step": 1}, session=session)
        await collection.insert_one({"step": 2}, session=session)

    assert await collection.count_documents({}) == 2
