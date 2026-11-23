from typing import Any

from httpx import AsyncClient
from pymongo.asynchronous.database import AsyncDatabase

from app.models.users import Role
from scripts.seed_users import DEMO_USERS, seed_users
from scripts.set_role import set_role
from tests.helpers import DEFAULT_PASSWORD, login, make_user

type Db = AsyncDatabase[dict[str, Any]]


async def test_seed_creates_one_account_per_role_that_can_sign_in(
    client: AsyncClient, db: Db
) -> None:
    results = await seed_users(db, DEFAULT_PASSWORD)

    assert [outcome for _, outcome in results] == ["created"] * 3
    for email, _, role in DEMO_USERS:
        stored = await db.users.find_one({"email": email})
        assert stored is not None
        assert stored["role"] == role.value
        assert await login(client, email)


async def test_seed_twice_keeps_passwords_and_restores_roles(client: AsyncClient, db: Db) -> None:
    await seed_users(db, DEFAULT_PASSWORD)
    await db.users.update_one({"email": "admin@example.com"}, {"$set": {"role": "attendee"}})

    results = await seed_users(db, "a-different-password")

    assert [outcome for _, outcome in results] == ["exists"] * 3
    assert await db.users.count_documents({}) == 3
    admin = await db.users.find_one({"email": "admin@example.com"})
    assert admin is not None
    assert admin["role"] == "admin"
    assert await login(client, "admin@example.com", DEFAULT_PASSWORD)


async def test_set_role_promotes_an_existing_account(db: Db) -> None:
    await make_user(db, email="ana@example.com")

    assert await set_role(db, " Ana@Example.com ", Role.ADMIN) is True

    stored = await db.users.find_one({"email": "ana@example.com"})
    assert stored is not None
    assert stored["role"] == "admin"


async def test_set_role_reports_an_unknown_email(db: Db) -> None:
    assert await set_role(db, "nobody@example.com", Role.ADMIN) is False
