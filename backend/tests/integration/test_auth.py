from collections.abc import AsyncIterator
from datetime import timedelta
from typing import Any

import jwt
import pytest
from bson import ObjectId
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from pymongo.asynchronous.database import AsyncDatabase

from app.auth.dependencies import OptionalUser, require_roles
from app.auth.tokens import ALGORITHM
from app.config import Settings
from app.errors import register_error_handlers
from app.models.users import Role
from app.utils.time import utcnow
from tests.helpers import DEFAULT_PASSWORD, bearer, login, make_user

type Db = AsyncDatabase[dict[str, Any]]

REGISTER = {"email": "Ana@Example.com", "password": DEFAULT_PASSWORD, "display_name": "Ana"}


# Register


async def test_register_creates_an_attendee(client: AsyncClient, db: Db) -> None:
    response = await client.post("/auth/register", json=REGISTER)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "ana@example.com"
    assert body["role"] == "attendee"
    assert "password_hash" not in body
    assert "password" not in body
    assert await db.users.count_documents({}) == 1


async def test_register_ignores_a_role_in_the_body(client: AsyncClient) -> None:
    response = await client.post("/auth/register", json={**REGISTER, "role": "admin"})

    assert response.status_code == 201
    assert response.json()["role"] == "attendee"


async def test_register_rejects_a_taken_email(client: AsyncClient) -> None:
    await client.post("/auth/register", json=REGISTER)

    response = await client.post("/auth/register", json={**REGISTER, "email": "ANA@example.com"})

    assert response.status_code == 409
    assert response.json()["code"] == "EMAIL_TAKEN"


@pytest.mark.parametrize(
    "change",
    [{"email": "nope"}, {"password": "short"}, {"display_name": "A"}],
    ids=["email", "password", "display_name"],
)
async def test_register_validates_fields(client: AsyncClient, change: dict[str, str]) -> None:
    response = await client.post("/auth/register", json={**REGISTER, **change})

    assert response.status_code == 422


# Login


async def test_login_returns_an_access_token_and_the_user(client: AsyncClient, db: Db) -> None:
    user = await make_user(db, email="ana@example.com")

    response = await client.post(
        "/auth/login", json={"email": "  ANA@example.com ", "password": DEFAULT_PASSWORD}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 15 * 60
    assert body["user"]["id"] == str(user["_id"])
    assert "password_hash" not in body["user"]


async def test_wrong_password_and_unknown_email_get_the_same_answer(
    client: AsyncClient, db: Db
) -> None:
    await make_user(db, email="ana@example.com")

    wrong_password = await client.post(
        "/auth/login", json={"email": "ana@example.com", "password": "not-the-password"}
    )
    unknown_email = await client.post(
        "/auth/login", json={"email": "nobody@example.com", "password": DEFAULT_PASSWORD}
    )

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()
    assert wrong_password.json()["code"] == "INVALID_CREDENTIALS"


# /auth/me


async def test_me_returns_the_signed_in_user(client: AsyncClient, db: Db) -> None:
    await make_user(db, email="ana@example.com", role=Role.ORGANIZER)
    token = await login(client, "ana@example.com")

    response = await client.get("/auth/me", headers=bearer(token))

    assert response.status_code == 200
    assert response.json()["email"] == "ana@example.com"
    assert response.json()["role"] == "organizer"


async def test_me_reads_the_role_from_the_database(client: AsyncClient, db: Db) -> None:
    user = await make_user(db, email="ana@example.com")
    token = await login(client, "ana@example.com")

    await db.users.update_one({"_id": user["_id"]}, {"$set": {"role": "admin"}})
    response = await client.get("/auth/me", headers=bearer(token))

    assert response.json()["role"] == "admin"


async def test_me_without_a_token_is_401(client: AsyncClient) -> None:
    response = await client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["code"] == "NOT_AUTHENTICATED"
    assert response.headers["www-authenticate"] == "Bearer"


async def test_me_with_a_malformed_token_is_401(client: AsyncClient) -> None:
    response = await client.get("/auth/me", headers=bearer("not-a-jwt"))

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_TOKEN"


async def test_me_with_an_expired_token_is_401(
    client: AsyncClient, db: Db, settings: Settings
) -> None:
    user = await make_user(db)
    past = utcnow() - timedelta(hours=1)
    claims = {"sub": str(user["_id"]), "type": "access", "iat": past, "exp": past}
    token = jwt.encode(claims, settings.jwt_secret, algorithm=ALGORITHM)

    response = await client.get("/auth/me", headers=bearer(token))

    assert response.status_code == 401
    assert response.json()["code"] == "TOKEN_EXPIRED"


async def test_me_for_a_deleted_account_is_401(client: AsyncClient, db: Db) -> None:
    user = await make_user(db, email="ana@example.com")
    token = await login(client, "ana@example.com")

    await db.users.delete_one({"_id": user["_id"]})
    response = await client.get("/auth/me", headers=bearer(token))

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_TOKEN"


async def test_me_with_a_valid_token_for_a_non_objectid_subject_is_401(
    client: AsyncClient, settings: Settings
) -> None:
    now = utcnow()
    claims = {"sub": "not-an-id", "type": "access", "iat": now, "exp": now + timedelta(minutes=5)}
    token = jwt.encode(claims, settings.jwt_secret, algorithm=ALGORITHM)

    response = await client.get("/auth/me", headers=bearer(token))

    assert response.status_code == 401


# Role guard and optional user, on a small app that shares the test database


@pytest.fixture
async def guarded(app: FastAPI) -> AsyncIterator[AsyncClient]:
    probe = FastAPI()
    probe.state = app.state  # same settings and database as the main app
    register_error_handlers(probe)

    @probe.get("/admin-only", dependencies=[Depends(require_roles(Role.ADMIN))])
    async def admin_only() -> dict[str, bool]:
        return {"ok": True}

    @probe.get("/whoami")
    async def whoami(user: OptionalUser) -> dict[str, str | None]:
        return {"email": user["email"] if user else None}

    async with AsyncClient(transport=ASGITransport(app=probe), base_url="http://test") as c:
        yield c


@pytest.mark.parametrize(
    ("role", "status"),
    [(Role.ADMIN, 200), (Role.ORGANIZER, 403), (Role.ATTENDEE, 403)],
)
async def test_require_roles_per_role(
    client: AsyncClient, guarded: AsyncClient, db: Db, role: Role, status: int
) -> None:
    await make_user(db, email=f"{role.value}@example.com", role=role)
    token = await login(client, f"{role.value}@example.com")

    response = await guarded.get("/admin-only", headers=bearer(token))

    assert response.status_code == status
    if status == 403:
        assert response.json()["code"] == "FORBIDDEN_ROLE"


async def test_require_roles_without_a_token_is_401(guarded: AsyncClient) -> None:
    response = await guarded.get("/admin-only")

    assert response.status_code == 401


async def test_optional_user_is_none_for_guests_and_set_when_signed_in(
    client: AsyncClient, guarded: AsyncClient, db: Db
) -> None:
    await make_user(db, email="ana@example.com")
    token = await login(client, "ana@example.com")

    guest = await guarded.get("/whoami")
    signed_in = await guarded.get("/whoami", headers=bearer(token))
    bad_token = await guarded.get("/whoami", headers=bearer("not-a-jwt"))

    assert guest.json() == {"email": None}
    assert signed_in.json() == {"email": "ana@example.com"}
    assert bad_token.status_code == 401


async def test_unknown_object_id_in_token_is_401(client: AsyncClient, settings: Settings) -> None:
    now = utcnow()
    claims = {
        "sub": str(ObjectId()),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }
    token = jwt.encode(claims, settings.jwt_secret, algorithm=ALGORITHM)

    response = await client.get("/auth/me", headers=bearer(token))

    assert response.status_code == 401
