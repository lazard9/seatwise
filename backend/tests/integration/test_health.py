from typing import Any

from httpx import ASGITransport, AsyncClient
from pymongo.asynchronous.database import AsyncDatabase

from app.main import create_app
from tests.conftest import TEST_DATABASE, make_settings


async def test_health_reports_ok_when_database_is_reachable(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


async def test_health_returns_503_when_database_is_unreachable() -> None:
    # Port 1 has no MongoDB; a short timeout keeps the test fast.
    settings = make_settings(mongodb_url="mongodb://127.0.0.1:1/", mongodb_timeout_ms=200)
    app = create_app(settings)

    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "unavailable"}


async def test_tests_run_against_a_replica_set(db: AsyncDatabase[dict[str, Any]]) -> None:
    # Transactions need a replica set; fail loudly if tests run against a standalone server.
    hello = await db.command("hello")

    assert hello.get("setName"), "MongoDB is not running as a replica set"
    assert db.name == TEST_DATABASE


async def test_transactions_work_on_the_test_database(
    db: AsyncDatabase[dict[str, Any]],
) -> None:
    collection = db["transaction_check"]
    await collection.delete_many({})

    async with db.client.start_session() as session, await session.start_transaction():
        await collection.insert_one({"step": 1}, session=session)
        await collection.insert_one({"step": 2}, session=session)

    assert await collection.count_documents({}) == 2
    await collection.drop()
