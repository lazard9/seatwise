"""Admin user management: GET /users and PATCH /users/{id}/role."""

from datetime import timedelta
from typing import Any

import pytest
from bson import ObjectId
from httpx import AsyncClient
from pymongo.asynchronous.database import AsyncDatabase

from app.models.users import Role
from tests.helpers import bearer, login, make_user

type Db = AsyncDatabase[dict[str, Any]]

ADMIN = "admin@example.com"


@pytest.fixture
async def admin_token(client: AsyncClient, db: Db) -> str:
    await make_user(db, email=ADMIN, role=Role.ADMIN, display_name="Admin")
    return await login(client, ADMIN)


async def token_for(client: AsyncClient, db: Db, role: Role) -> str:
    email = f"{role.value}-caller@example.com"
    await make_user(db, email=email, role=role)
    return await login(client, email)


# Permission matrix: "Manage users and roles" is admin only


@pytest.mark.parametrize(
    ("role", "status"),
    [(Role.ADMIN, 200), (Role.ORGANIZER, 403), (Role.ATTENDEE, 403)],
)
async def test_list_users_per_role(client: AsyncClient, db: Db, role: Role, status: int) -> None:
    token = await token_for(client, db, role)

    response = await client.get("/users", headers=bearer(token))

    assert response.status_code == status
    if status == 403:
        assert response.json()["code"] == "FORBIDDEN_ROLE"


@pytest.mark.parametrize(
    ("role", "status"),
    [(Role.ADMIN, 200), (Role.ORGANIZER, 403), (Role.ATTENDEE, 403)],
)
async def test_change_role_per_role(client: AsyncClient, db: Db, role: Role, status: int) -> None:
    token = await token_for(client, db, role)
    target = await make_user(db, email="target@example.com")

    response = await client.patch(
        f"/users/{target['_id']}/role", json={"role": "organizer"}, headers=bearer(token)
    )

    assert response.status_code == status
    stored = await db.users.find_one({"_id": target["_id"]})
    assert stored is not None
    assert stored["role"] == ("organizer" if status == 200 else "attendee")


async def test_anonymous_gets_401_on_both_routes(client: AsyncClient, db: Db) -> None:
    target = await make_user(db, email="target@example.com")

    listing = await client.get("/users")
    change = await client.patch(f"/users/{target['_id']}/role", json={"role": "admin"})

    assert listing.status_code == change.status_code == 401


# GET /users


async def test_list_returns_public_fields_newest_first(
    client: AsyncClient, db: Db, admin_token: str
) -> None:
    older = await make_user(db, email="older@example.com")
    await db.users.update_one(
        {"_id": older["_id"]}, {"$set": {"created_at": older["created_at"] - timedelta(days=1)}}
    )
    await make_user(db, email="newer@example.com")

    body = (await client.get("/users", headers=bearer(admin_token))).json()

    emails = [user["email"] for user in body["items"]]
    assert emails == ["newer@example.com", ADMIN, "older@example.com"]
    assert body["total"] == 3
    assert all("password_hash" not in user for user in body["items"])


async def test_list_is_paginated(client: AsyncClient, db: Db, admin_token: str) -> None:
    for i in range(4):
        await make_user(db, email=f"user{i}@example.com")

    first = (await client.get("/users?page=1&page_size=2", headers=bearer(admin_token))).json()
    third = (await client.get("/users?page=3&page_size=2", headers=bearer(admin_token))).json()

    assert first["total"] == third["total"] == 5
    assert len(first["items"]) == 2
    assert len(third["items"]) == 1
    assert (first["page"], first["page_size"]) == (1, 2)


async def test_pages_do_not_repeat_or_skip_users_with_equal_timestamps(
    client: AsyncClient, db: Db, admin_token: str
) -> None:
    for i in range(5):
        await make_user(db, email=f"same{i}@example.com")
    same_time = (await db.users.find_one({"email": ADMIN}) or {})["created_at"]
    await db.users.update_many({}, {"$set": {"created_at": same_time}})

    seen = []
    for page in (1, 2, 3):
        response = await client.get(f"/users?page={page}&page_size=2", headers=bearer(admin_token))
        seen += [user["id"] for user in response.json()["items"]]

    assert len(seen) == len(set(seen)) == 6


async def test_list_filters_by_role(client: AsyncClient, db: Db, admin_token: str) -> None:
    await make_user(db, email="org@example.com", role=Role.ORGANIZER)
    await make_user(db, email="att@example.com")

    body = (await client.get("/users?role=organizer", headers=bearer(admin_token))).json()

    assert [user["email"] for user in body["items"]] == ["org@example.com"]
    assert body["total"] == 1


async def test_search_matches_email_or_name_ignoring_case(
    client: AsyncClient, db: Db, admin_token: str
) -> None:
    await make_user(db, email="marko@example.com", display_name="Marko")
    await make_user(db, email="jelena@example.com", display_name="Jelena Markovic")
    await make_user(db, email="ivan@example.com", display_name="Ivan")

    body = (await client.get("/users?search=MARK", headers=bearer(admin_token))).json()

    assert {user["email"] for user in body["items"]} == {"marko@example.com", "jelena@example.com"}


async def test_search_text_is_literal_not_a_pattern(
    client: AsyncClient, db: Db, admin_token: str
) -> None:
    await make_user(db, email="axb@example.com")

    body = (await client.get("/users?search=a.b", headers=bearer(admin_token))).json()

    assert body["items"] == []


@pytest.mark.parametrize(
    "query", ["page=0", "page_size=0", "page_size=101", "role=superuser"], ids=lambda q: q
)
async def test_list_rejects_bad_query_params(
    client: AsyncClient, admin_token: str, query: str
) -> None:
    response = await client.get(f"/users?{query}", headers=bearer(admin_token))

    assert response.status_code == 422


# PATCH /users/{id}/role


async def test_admin_changes_a_role_and_it_applies_at_once(
    client: AsyncClient, db: Db, admin_token: str
) -> None:
    await make_user(db, email="ana@example.com")
    ana_token = await login(client, "ana@example.com")
    ana_id = (await client.get("/auth/me", headers=bearer(ana_token))).json()["id"]

    response = await client.patch(
        f"/users/{ana_id}/role", json={"role": "organizer"}, headers=bearer(admin_token)
    )

    assert response.status_code == 200
    assert response.json()["role"] == "organizer"
    assert "password_hash" not in response.json()
    # Ana's existing token now acts as an organizer: the role is read from the database.
    me = await client.get("/auth/me", headers=bearer(ana_token))
    assert me.json()["role"] == "organizer"


async def test_admin_can_promote_and_demote_another_admin(
    client: AsyncClient, db: Db, admin_token: str
) -> None:
    other = await make_user(db, email="other@example.com", role=Role.ADMIN)

    response = await client.patch(
        f"/users/{other['_id']}/role", json={"role": "attendee"}, headers=bearer(admin_token)
    )

    assert response.status_code == 200
    assert response.json()["role"] == "attendee"


async def test_admin_cannot_change_their_own_role(
    client: AsyncClient, db: Db, admin_token: str
) -> None:
    me = (await client.get("/auth/me", headers=bearer(admin_token))).json()

    response = await client.patch(
        f"/users/{me['id']}/role", json={"role": "attendee"}, headers=bearer(admin_token)
    )

    assert response.status_code == 403
    assert response.json()["code"] == "CANNOT_CHANGE_OWN_ROLE"
    stored = await db.users.find_one({"email": ADMIN})
    assert stored is not None
    assert stored["role"] == "admin"


async def test_setting_the_same_role_is_accepted(
    client: AsyncClient, db: Db, admin_token: str
) -> None:
    target = await make_user(db, email="target@example.com")

    response = await client.patch(
        f"/users/{target['_id']}/role", json={"role": "attendee"}, headers=bearer(admin_token)
    )

    assert response.status_code == 200


async def test_unknown_user_is_404(client: AsyncClient, admin_token: str) -> None:
    response = await client.patch(
        f"/users/{ObjectId()}/role", json={"role": "organizer"}, headers=bearer(admin_token)
    )

    assert response.status_code == 404
    assert response.json()["code"] == "USER_NOT_FOUND"


async def test_malformed_id_is_400(client: AsyncClient, admin_token: str) -> None:
    response = await client.patch(
        "/users/not-an-id/role", json={"role": "organizer"}, headers=bearer(admin_token)
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_ID"


@pytest.mark.parametrize("body", [{"role": "superuser"}, {}, {"role": None}])
async def test_invalid_role_is_422(
    client: AsyncClient, db: Db, admin_token: str, body: dict[str, Any]
) -> None:
    target = await make_user(db, email="target@example.com")

    response = await client.patch(
        f"/users/{target['_id']}/role", json=body, headers=bearer(admin_token)
    )

    assert response.status_code == 422
