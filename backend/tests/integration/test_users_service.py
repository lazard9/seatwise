import asyncio
from datetime import UTC
from typing import Any

import pytest
from pymongo.asynchronous.database import AsyncDatabase

from app.auth.passwords import verify_password
from app.errors import Conflict
from app.models.users import Role, UserCreate
from app.services.users import create_user, find_user_by_email, serialize_user

type Db = AsyncDatabase[dict[str, Any]]


def new_user(email: str = "ana@example.com") -> UserCreate:
    return UserCreate(email=email, password="long-enough", display_name="Ana")


async def test_create_user_stores_a_hash_and_defaults_to_attendee(db: Db) -> None:
    doc = await create_user(db.users, new_user())

    stored = await db.users.find_one({"_id": doc["_id"]})
    assert stored is not None
    assert stored["role"] == "attendee"
    assert stored["password_hash"] != "long-enough"
    assert verify_password(stored["password_hash"], "long-enough")
    assert stored["created_at"].tzinfo is not None
    assert stored["created_at"].utcoffset() == UTC.utcoffset(None)


async def test_create_user_with_explicit_role(db: Db) -> None:
    doc = await create_user(db.users, new_user(), role=Role.ORGANIZER)

    assert doc["role"] == "organizer"


async def test_duplicate_email_is_rejected_regardless_of_case(db: Db) -> None:
    await create_user(db.users, new_user("ana@example.com"))

    with pytest.raises(Conflict) as info:
        await create_user(db.users, new_user("ANA@Example.com"))

    assert info.value.code == "EMAIL_TAKEN"
    assert await db.users.count_documents({}) == 1


async def test_simultaneous_sign_ups_with_one_email_create_one_user(db: Db) -> None:
    results = await asyncio.gather(
        *(create_user(db.users, new_user()) for _ in range(5)),
        return_exceptions=True,
    )

    assert sum(isinstance(r, dict) for r in results) == 1
    assert sum(isinstance(r, Conflict) for r in results) == 4
    assert await db.users.count_documents({}) == 1


async def test_find_user_by_email_ignores_case_and_spaces(db: Db) -> None:
    await create_user(db.users, new_user("ana@example.com"))

    found = await find_user_by_email(db.users, "  Ana@Example.com ")

    assert found is not None
    assert found["email"] == "ana@example.com"


async def test_find_user_by_email_returns_none_when_missing(db: Db) -> None:
    assert await find_user_by_email(db.users, "nobody@example.com") is None


async def test_serialized_user_has_no_password_hash(db: Db) -> None:
    doc = await create_user(db.users, new_user())

    public = serialize_user(doc).model_dump()

    assert "password_hash" not in public
    assert public["id"] == str(doc["_id"])
    assert public["role"] == "attendee"
