"""Refresh rotation, reuse detection, the two-tab grace period, and logout."""

import asyncio
from datetime import timedelta
from typing import Any

import pytest
from bson import ObjectId
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Response
from pymongo.asynchronous.database import AsyncDatabase

from app.auth.cookies import REFRESH_COOKIE
from app.auth.tokens import hash_refresh_token
from app.services.sessions import revoke_family
from app.utils.time import utcnow
from tests.helpers import bearer, login_session, make_user, refresh_cookie

type Db = AsyncDatabase[dict[str, Any]]

EMAIL = "ana@example.com"


async def post_with_cookie(app: FastAPI, path: str, token: str | None) -> Response:
    """Send one request carrying exactly this refresh cookie, like a browser tab.

    A fresh client per call, so no cookie jar adds or replaces anything.
    """
    headers = {"Cookie": f"{REFRESH_COOKIE}={token}"} if token else {}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        return await c.post(path, headers=headers)


async def refresh(app: FastAPI, token: str | None) -> Response:
    return await post_with_cookie(app, "/auth/refresh", token)


async def logout(app: FastAPI, token: str | None) -> Response:
    return await post_with_cookie(app, "/auth/logout", token)


async def token_doc(db: Db, token: str) -> dict[str, Any]:
    doc = await db.refresh_tokens.find_one({"token_hash": hash_refresh_token(token)})
    assert doc is not None
    return doc


async def age_last_use(db: Db, token: str, seconds: int) -> None:
    """Pretend the token was rotated `seconds` ago, instead of sleeping in the test."""
    used_at = utcnow() - timedelta(seconds=seconds)
    await db.refresh_tokens.update_one(
        {"token_hash": hash_refresh_token(token)}, {"$set": {"used_at": used_at}}
    )


def assert_cookie_cleared(response: Response) -> None:
    header = response.headers["set-cookie"].lower()
    assert header.startswith(f"{REFRESH_COOKIE}=")
    assert "max-age=0" in header


@pytest.fixture
async def user(db: Db) -> dict[str, Any]:
    return await make_user(db, email=EMAIL)


# Login


async def test_login_sets_an_httponly_refresh_cookie(client: AsyncClient, user: Any) -> None:
    response = await client.post(
        "/auth/login", json={"email": EMAIL, "password": "long-enough-password"}
    )

    header = response.headers["set-cookie"].lower()
    assert "httponly" in header
    assert "samesite=lax" in header
    assert "path=/auth" in header
    assert REFRESH_COOKIE not in response.text  # never in the body


async def test_only_a_hash_of_the_refresh_token_is_stored(
    client: AsyncClient, db: Db, user: Any
) -> None:
    _, token = await login_session(client, EMAIL)

    doc = await token_doc(db, token)

    assert token not in {str(value) for value in doc.values()}
    assert doc["user_id"] == user["_id"]
    assert doc["used_at"] is None
    assert doc["revoked_at"] is None


async def test_each_login_starts_its_own_family(client: AsyncClient, db: Db, user: Any) -> None:
    _, laptop = await login_session(client, EMAIL)
    _, phone = await login_session(client, EMAIL)

    assert (await token_doc(db, laptop))["family_id"] != (await token_doc(db, phone))["family_id"]


# Rotation


async def test_refresh_rotates_the_cookie_and_returns_an_access_token(
    app: FastAPI, client: AsyncClient, db: Db, user: Any
) -> None:
    _, first = await login_session(client, EMAIL)

    response = await refresh(app, first)

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == EMAIL
    second = refresh_cookie(response)
    assert second != first
    assert (await token_doc(db, first))["used_at"] is not None
    assert (await token_doc(db, second))["family_id"] == (await token_doc(db, first))["family_id"]
    me = await client.get("/auth/me", headers=bearer(body["access_token"]))
    assert me.status_code == 200


async def test_a_chain_of_refreshes_keeps_working(
    app: FastAPI, client: AsyncClient, user: Any
) -> None:
    _, token = await login_session(client, EMAIL)

    for _ in range(3):
        response = await refresh(app, token)
        assert response.status_code == 200
        token = refresh_cookie(response)


async def test_refresh_extends_the_session(
    app: FastAPI, client: AsyncClient, db: Db, user: Any
) -> None:
    _, first = await login_session(client, EMAIL)
    await db.refresh_tokens.update_one(
        {"token_hash": hash_refresh_token(first)},
        {"$set": {"expires_at": utcnow() + timedelta(hours=1)}},
    )

    second = refresh_cookie(await refresh(app, first))

    assert (await token_doc(db, second))["expires_at"] > utcnow() + timedelta(days=6)


# Rejected refreshes


async def test_refresh_without_a_cookie_is_401(app: FastAPI) -> None:
    response = await refresh(app, None)

    assert response.status_code == 401
    assert response.json()["code"] == "NOT_AUTHENTICATED"
    assert_cookie_cleared(response)


async def test_refresh_with_an_unknown_token_is_401_and_clears_the_cookie(app: FastAPI) -> None:
    response = await refresh(app, "made-up-token")

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_REFRESH_TOKEN"
    assert_cookie_cleared(response)


async def test_refresh_with_an_expired_token_is_401(
    app: FastAPI, client: AsyncClient, db: Db, user: Any
) -> None:
    _, token = await login_session(client, EMAIL)
    await db.refresh_tokens.update_one(
        {"token_hash": hash_refresh_token(token)},
        {"$set": {"expires_at": utcnow() - timedelta(seconds=1)}},
    )

    response = await refresh(app, token)

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_REFRESH_TOKEN"


async def test_refresh_for_a_deleted_account_is_401(
    app: FastAPI, client: AsyncClient, db: Db, user: Any
) -> None:
    _, token = await login_session(client, EMAIL)
    await db.users.delete_one({"_id": user["_id"]})

    response = await refresh(app, token)

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_REFRESH_TOKEN"


# Reuse detection


async def test_reusing_a_rotated_token_revokes_the_whole_family(
    app: FastAPI, client: AsyncClient, db: Db, user: Any
) -> None:
    _, stolen = await login_session(client, EMAIL)
    current = refresh_cookie(await refresh(app, stolen))  # the real user moved on
    await age_last_use(db, stolen, seconds=11)

    reuse = await refresh(app, stolen)

    assert reuse.status_code == 401
    assert reuse.json()["code"] == "REFRESH_TOKEN_REUSED"
    assert_cookie_cleared(reuse)
    # The legitimate token is dead too: nobody knows which side is the thief.
    after = await refresh(app, current)
    assert after.status_code == 401
    assert after.json()["code"] == "INVALID_REFRESH_TOKEN"
    family_id = (await token_doc(db, stolen))["family_id"]
    assert (
        await db.refresh_tokens.count_documents({"family_id": family_id, "revoked_at": None}) == 0
    )


async def test_reuse_does_not_touch_other_devices(
    app: FastAPI, client: AsyncClient, db: Db, user: Any
) -> None:
    _, stolen = await login_session(client, EMAIL)
    _, phone = await login_session(client, EMAIL)
    await refresh(app, stolen)
    await age_last_use(db, stolen, seconds=11)

    await refresh(app, stolen)

    assert (await refresh(app, phone)).status_code == 200


async def test_reuse_racing_a_legitimate_refresh_leaves_no_live_token(
    app: FastAPI, client: AsyncClient, db: Db, user: Any
) -> None:
    _, stolen = await login_session(client, EMAIL)
    current = refresh_cookie(await refresh(app, stolen))
    await age_last_use(db, stolen, seconds=11)

    await asyncio.gather(refresh(app, stolen), refresh(app, current))

    family_id = (await token_doc(db, stolen))["family_id"]
    assert (
        await db.refresh_tokens.count_documents({"family_id": family_id, "revoked_at": None}) == 0
    )


# Two tabs: the grace period


async def test_a_rotated_token_is_accepted_within_the_grace_period(
    app: FastAPI, client: AsyncClient, db: Db, user: Any
) -> None:
    _, first = await login_session(client, EMAIL)
    tab_a = await refresh(app, first)
    await age_last_use(db, first, seconds=5)

    tab_b = await refresh(app, first)

    assert tab_a.status_code == tab_b.status_code == 200
    # Both tabs can carry on with the token each one received.
    assert (await refresh(app, refresh_cookie(tab_a))).status_code == 200
    assert (await refresh(app, refresh_cookie(tab_b))).status_code == 200


async def test_tabs_refreshing_at_the_same_moment_all_stay_signed_in(
    app: FastAPI, client: AsyncClient, db: Db, user: Any
) -> None:
    _, shared = await login_session(client, EMAIL)

    responses = await asyncio.gather(*(refresh(app, shared) for _ in range(5)))

    assert [r.status_code for r in responses] == [200] * 5
    new_tokens = {refresh_cookie(r) for r in responses}
    assert len(new_tokens) == 5
    family_id = (await token_doc(db, shared))["family_id"]
    assert (
        await db.refresh_tokens.count_documents({"family_id": family_id, "revoked_at": None}) == 6
    )
    for token in new_tokens:
        assert (await refresh(app, token)).status_code == 200


# Logout


async def test_logout_ends_this_session_only(
    app: FastAPI, client: AsyncClient, db: Db, user: Any
) -> None:
    _, laptop = await login_session(client, EMAIL)
    _, phone = await login_session(client, EMAIL)

    response = await logout(app, laptop)

    assert response.status_code == 204
    assert_cookie_cleared(response)
    assert (await refresh(app, laptop)).json()["code"] == "INVALID_REFRESH_TOKEN"
    assert (await refresh(app, phone)).status_code == 200


async def test_logout_revokes_tokens_issued_after_login(
    app: FastAPI, client: AsyncClient, user: Any
) -> None:
    _, first = await login_session(client, EMAIL)
    second = refresh_cookie(await refresh(app, first))

    await logout(app, first)

    assert (await refresh(app, second)).status_code == 401


@pytest.mark.parametrize("token", [None, "made-up-token"], ids=["no-cookie", "unknown"])
async def test_logout_always_succeeds(app: FastAPI, token: str | None) -> None:
    response = await logout(app, token)

    assert response.status_code == 204
    assert_cookie_cleared(response)


# Storage


async def test_expired_rows_are_removed_by_a_ttl_index(db: Db) -> None:
    indexes = await db.refresh_tokens.index_information()

    assert indexes["expires_at_ttl"]["expireAfterSeconds"] == 0
    assert indexes["token_hash_unique"]["unique"] is True


async def test_revoking_an_unknown_family_is_harmless(db: Db) -> None:
    await revoke_family(db, ObjectId())

    assert await db.refresh_tokens.count_documents({}) == 0
