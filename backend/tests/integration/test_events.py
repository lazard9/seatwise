"""Events: create, read, edit, publish, cancel, delete.

Rules come from brief section 6, permission rows from section 7.
"""

import asyncio
from datetime import timedelta
from typing import Any

import pytest
from bson import ObjectId
from httpx import AsyncClient
from pymongo.asynchronous.database import AsyncDatabase

from app.models.events import EventWrite
from app.models.users import Role
from app.services.events import create_event
from app.utils.time import utcnow
from tests.helpers import bearer, login, make_user

type Db = AsyncDatabase[dict[str, Any]]

OWNER = "owner@example.com"


def payload(**overrides: Any) -> dict[str, Any]:
    starts = utcnow() + timedelta(days=10)
    data: dict[str, Any] = {
        "title": "Jazz Night",
        "description": "Live jazz in the garden.",
        "category": "music",
        "city": "Novi Sad",
        "venue": "Garden Club",
        "address": "Dunavska 1",
        "starts_at": starts.isoformat(),
        "ends_at": (starts + timedelta(hours=3)).isoformat(),
        "capacity": 50,
        "price": 1200,
    }
    data.update(overrides)
    return data


async def caller(client: AsyncClient, db: Db, role: Role, email: str | None = None) -> str:
    """Create a user with `role` and return their access token."""
    email = email or f"{role.value}-caller@example.com"
    await make_user(db, email=email, role=role)
    return await login(client, email)


async def make_event(db: Db, status: str = "draft", **changes: Any) -> dict[str, Any]:
    """An event owned by OWNER, created through the service, then changed directly."""
    owner = await db.users.find_one({"email": OWNER}) or await make_user(
        db, email=OWNER, role=Role.ORGANIZER, display_name="Owner"
    )
    event = await create_event(db.events, EventWrite(**payload()), owner)
    changes = {"status": status, **changes}
    await db.events.update_one({"_id": event["_id"]}, {"$set": changes})
    return {**event, **changes}


async def headers_for(client: AsyncClient, db: Db, who: str) -> dict[str, str]:
    """Headers for one of: admin, owner, other (another organizer), attendee, anonymous."""
    if who == "anonymous":
        return {}
    if who == "owner":
        if await db.users.find_one({"email": OWNER}) is None:
            await make_user(db, email=OWNER, role=Role.ORGANIZER, display_name="Owner")
        return bearer(await login(client, OWNER))
    role = {"admin": Role.ADMIN, "other": Role.ORGANIZER, "attendee": Role.ATTENDEE}[who]
    return bearer(await caller(client, db, role))


def past_times() -> dict[str, Any]:
    ended = utcnow() - timedelta(days=1)
    return {"starts_at": ended - timedelta(hours=2), "ends_at": ended}


async def add_reservation(db: Db, event_id: ObjectId, status: str = "confirmed") -> ObjectId:
    result = await db.reservations.insert_one(
        {
            "event_id": event_id,
            "user_id": ObjectId(),
            "seats": 2,
            "status": status,
            "created_at": utcnow(),
            "cancelled_at": None,
            "cancelled_by": None,
        }
    )
    return result.inserted_id


async def stored(db: Db, event_id: ObjectId) -> dict[str, Any]:
    doc = await db.events.find_one({"_id": event_id})
    assert doc is not None
    return doc


# Create


async def test_create_makes_a_draft_owned_by_the_caller(client: AsyncClient, db: Db) -> None:
    headers = await headers_for(client, db, "owner")
    owner = await db.users.find_one({"email": OWNER})
    assert owner is not None

    response = await client.post(
        "/events",
        json=payload(organizer_id=str(ObjectId()), seats_taken=40, status="published"),
        headers=headers,
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "draft"
    assert body["organizer_id"] == str(owner["_id"])
    assert body["seats_taken"] == 0
    assert body["seats_left"] == 50
    assert body["slug"] == "jazz-night"
    assert body["is_past"] is False
    assert body["rating_avg"] == 0
    assert body["rating_count"] == 0
    assert body["image"] is None
    assert "image_public_id" not in body


# Matrix: "Create event" is admin and organizer.
@pytest.mark.parametrize(
    ("who", "status"),
    [("admin", 201), ("other", 201), ("attendee", 403), ("anonymous", 401)],
)
async def test_create_per_role(client: AsyncClient, db: Db, who: str, status: int) -> None:
    headers = await headers_for(client, db, who)

    response = await client.post("/events", json=payload(), headers=headers)

    assert response.status_code == status
    assert await db.events.count_documents({}) == (1 if status == 201 else 0)


async def test_create_rejects_a_start_in_the_past(client: AsyncClient, db: Db) -> None:
    headers = await headers_for(client, db, "owner")
    start = utcnow() - timedelta(minutes=1)
    times = {"starts_at": start.isoformat(), "ends_at": (start + timedelta(hours=1)).isoformat()}

    response = await client.post("/events", json=payload(**times), headers=headers)

    assert response.status_code == 422
    assert response.json()["code"] == "STARTS_IN_PAST"


async def test_create_rejects_an_end_before_the_start(client: AsyncClient, db: Db) -> None:
    headers = await headers_for(client, db, "owner")
    data = payload()

    response = await client.post(
        "/events", json={**data, "ends_at": data["starts_at"]}, headers=headers
    )

    assert response.status_code == 422


async def test_same_title_gets_numbered_slugs(client: AsyncClient, db: Db) -> None:
    headers = await headers_for(client, db, "owner")
    titles = ["Đorđe Balašević", "Ђорђе Балашевић", "djordje balasevic"]

    slugs = [
        (await client.post("/events", json=payload(title=title), headers=headers)).json()["slug"]
        for title in titles
    ]

    assert slugs == ["djordje-balasevic", "djordje-balasevic-2", "djordje-balasevic-3"]


async def test_simultaneous_creates_get_distinct_slugs(client: AsyncClient, db: Db) -> None:
    headers = await headers_for(client, db, "owner")

    responses = await asyncio.gather(
        *(client.post("/events", json=payload(), headers=headers) for _ in range(5))
    )

    assert [r.status_code for r in responses] == [201] * 5
    slugs = {r.json()["slug"] for r in responses}
    assert slugs == {"jazz-night", "jazz-night-2", "jazz-night-3", "jazz-night-4", "jazz-night-5"}


# Read


@pytest.mark.parametrize("event_status", ["published", "cancelled"])
@pytest.mark.parametrize("who", ["admin", "owner", "other", "attendee", "anonymous"])
async def test_published_and_cancelled_events_are_public(
    client: AsyncClient, db: Db, event_status: str, who: str
) -> None:
    # A cancelled event stays readable, so people with its link learn that it was cancelled.
    event = await make_event(db, status=event_status)
    headers = await headers_for(client, db, who)

    by_id = await client.get(f"/events/{event['_id']}", headers=headers)
    by_slug = await client.get(f"/events/by-slug/{event['slug']}", headers=headers)

    assert by_id.status_code == by_slug.status_code == 200
    assert by_id.json() == by_slug.json()
    assert by_id.json()["status"] == event_status


# Matrix: "See drafts" is all for admin, own for organizer, none for attendee and anonymous.
@pytest.mark.parametrize(
    ("who", "status"),
    [("admin", 200), ("owner", 200), ("other", 404), ("attendee", 404), ("anonymous", 404)],
)
async def test_draft_per_role(client: AsyncClient, db: Db, who: str, status: int) -> None:
    event = await make_event(db)
    headers = await headers_for(client, db, who)

    by_id = await client.get(f"/events/{event['_id']}", headers=headers)
    by_slug = await client.get(f"/events/by-slug/{event['slug']}", headers=headers)

    assert by_id.status_code == by_slug.status_code == status
    if status == 404:
        assert by_id.json()["code"] == by_slug.json()["code"] == "EVENT_NOT_FOUND"


async def test_get_with_a_malformed_or_unknown_id(client: AsyncClient) -> None:
    malformed = await client.get("/events/not-an-id")
    unknown = await client.get(f"/events/{ObjectId()}")
    unknown_slug = await client.get("/events/by-slug/nothing-here")

    assert malformed.status_code == 400
    assert malformed.json()["code"] == "INVALID_ID"
    assert unknown.status_code == unknown_slug.status_code == 404


async def test_is_past_follows_the_end(client: AsyncClient, db: Db) -> None:
    now = utcnow()
    running = await make_event(
        db, status="published", starts_at=now - timedelta(hours=1), ends_at=now + timedelta(hours=1)
    )
    ended = await make_event(db, status="published", **past_times())

    assert (await client.get(f"/events/{running['_id']}")).json()["is_past"] is False
    assert (await client.get(f"/events/{ended['_id']}")).json()["is_past"] is True


# Edit


# Matrix: "Edit event" is all for admin, own for organizer.
@pytest.mark.parametrize(
    ("who", "status", "code"),
    [
        ("admin", 200, None),
        ("owner", 200, None),
        ("other", 403, "NOT_EVENT_OWNER"),
        ("attendee", 403, "FORBIDDEN_ROLE"),
        ("anonymous", 401, "NOT_AUTHENTICATED"),
    ],
)
async def test_edit_per_role(
    client: AsyncClient, db: Db, who: str, status: int, code: str | None
) -> None:
    event = await make_event(db, status="published")
    headers = await headers_for(client, db, who)

    response = await client.put(
        f"/events/{event['_id']}", json=payload(title="Blues Night"), headers=headers
    )

    assert response.status_code == status
    if code:
        assert response.json()["code"] == code
    title = (await stored(db, event["_id"]))["title"]
    assert title == ("Blues Night" if status == 200 else "Jazz Night")


async def test_edit_keeps_slug_status_seats_and_owner(client: AsyncClient, db: Db) -> None:
    event = await make_event(db, status="published", seats_taken=5)
    headers = await headers_for(client, db, "owner")
    ignored = {"status": "draft", "seats_taken": 0, "organizer_id": str(ObjectId())}

    response = await client.put(
        f"/events/{event['_id']}", json=payload(title="Blues Night", **ignored), headers=headers
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["title"] == "Blues Night"
    assert body["slug"] == "jazz-night"
    assert body["status"] == "published"
    assert body["seats_taken"] == 5
    assert body["organizer_id"] == str(event["organizer_id"])
    assert body["updated_at"] > body["created_at"]


async def test_capacity_cannot_drop_below_seats_taken(client: AsyncClient, db: Db) -> None:
    event = await make_event(db, status="published", seats_taken=20)
    headers = await headers_for(client, db, "owner")
    url = f"/events/{event['_id']}"

    below = await client.put(url, json=payload(capacity=19), headers=headers)
    equal = await client.put(url, json=payload(capacity=20), headers=headers)

    assert below.status_code == 409
    assert below.json()["code"] == "CAPACITY_BELOW_SEATS_TAKEN"
    assert equal.status_code == 200
    assert equal.json()["seats_left"] == 0


@pytest.mark.parametrize(("who", "status"), [("owner", 403), ("admin", 200)])
async def test_past_event_is_edited_only_by_admin(
    client: AsyncClient, db: Db, who: str, status: int
) -> None:
    event = await make_event(db, status="published", **past_times())
    headers = await headers_for(client, db, who)

    response = await client.put(f"/events/{event['_id']}", json=payload(), headers=headers)

    assert response.status_code == status
    if status == 403:
        assert response.json()["code"] == "EVENT_PAST"


async def test_cancelled_event_cannot_be_edited(client: AsyncClient, db: Db) -> None:
    event = await make_event(db, status="cancelled")
    headers = await headers_for(client, db, "owner")

    response = await client.put(f"/events/{event['_id']}", json=payload(), headers=headers)

    assert response.status_code == 409
    assert response.json()["code"] == "EVENT_CANCELLED"


# Publish


@pytest.mark.parametrize(
    ("who", "status"),
    [("admin", 200), ("owner", 200), ("other", 404), ("attendee", 403), ("anonymous", 401)],
)
async def test_publish_per_role(client: AsyncClient, db: Db, who: str, status: int) -> None:
    event = await make_event(db)
    headers = await headers_for(client, db, who)

    response = await client.post(f"/events/{event['_id']}/publish", headers=headers)

    assert response.status_code == status
    expected = "published" if status == 200 else "draft"
    assert (await stored(db, event["_id"]))["status"] == expected


@pytest.mark.parametrize("event_status", ["published", "cancelled"])
async def test_only_a_draft_can_be_published(
    client: AsyncClient, db: Db, event_status: str
) -> None:
    event = await make_event(db, status=event_status)
    headers = await headers_for(client, db, "owner")

    response = await client.post(f"/events/{event['_id']}/publish", headers=headers)

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_TRANSITION"


# Cancel


# Matrix: "Cancel event" is all for admin, own for organizer.
@pytest.mark.parametrize(
    ("who", "status"),
    [("admin", 200), ("owner", 200), ("other", 403), ("attendee", 403), ("anonymous", 401)],
)
async def test_cancel_per_role(client: AsyncClient, db: Db, who: str, status: int) -> None:
    event = await make_event(db, status="published")
    headers = await headers_for(client, db, who)

    response = await client.post(f"/events/{event['_id']}/cancel", headers=headers)

    assert response.status_code == status
    expected = "cancelled" if status == 200 else "published"
    assert (await stored(db, event["_id"]))["status"] == expected


async def test_cancel_cancels_confirmed_reservations_of_that_event(
    client: AsyncClient, db: Db
) -> None:
    event = await make_event(db, status="published", seats_taken=4)
    other = await make_event(db, status="published")
    confirmed = await add_reservation(db, event["_id"])
    already = await add_reservation(db, event["_id"], status="cancelled")
    elsewhere = await add_reservation(db, other["_id"])
    headers = await headers_for(client, db, "owner")

    response = await client.post(f"/events/{event['_id']}/cancel", headers=headers)

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "cancelled"
    # Seats are not released: the event is gone.
    assert response.json()["seats_taken"] == 4
    by_id = {doc["_id"]: doc async for doc in db.reservations.find()}
    assert by_id[confirmed]["status"] == "cancelled"
    assert by_id[confirmed]["cancelled_by"] == "organizer"
    assert by_id[confirmed]["cancelled_at"] is not None
    assert by_id[already]["cancelled_by"] is None
    assert by_id[elsewhere]["status"] == "confirmed"


async def test_a_draft_can_be_cancelled_but_not_twice(client: AsyncClient, db: Db) -> None:
    event = await make_event(db)
    headers = await headers_for(client, db, "owner")
    url = f"/events/{event['_id']}/cancel"

    first = await client.post(url, headers=headers)
    second = await client.post(url, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 400
    assert second.json()["code"] == "INVALID_TRANSITION"


async def test_organizer_cannot_cancel_a_past_event(client: AsyncClient, db: Db) -> None:
    event = await make_event(db, status="published", **past_times())
    headers = await headers_for(client, db, "owner")

    response = await client.post(f"/events/{event['_id']}/cancel", headers=headers)

    assert response.status_code == 403
    assert response.json()["code"] == "EVENT_PAST"


# Delete


# Matrix: "Delete event" is admin only, not even the organizer of the event.
@pytest.mark.parametrize(
    ("who", "status"),
    [("admin", 204), ("owner", 403), ("attendee", 403), ("anonymous", 401)],
)
async def test_delete_per_role(client: AsyncClient, db: Db, who: str, status: int) -> None:
    event = await make_event(db, status="published")
    headers = await headers_for(client, db, who)

    response = await client.delete(f"/events/{event['_id']}", headers=headers)

    assert response.status_code == status
    assert await db.events.count_documents({}) == (0 if status == 204 else 1)


@pytest.mark.parametrize("reservation_status", ["confirmed", "cancelled"])
async def test_event_with_reservations_cannot_be_deleted(
    client: AsyncClient, db: Db, reservation_status: str
) -> None:
    event = await make_event(db, status="published")
    await add_reservation(db, event["_id"], status=reservation_status)
    headers = await headers_for(client, db, "admin")

    response = await client.delete(f"/events/{event['_id']}", headers=headers)

    assert response.status_code == 409
    assert response.json()["code"] == "EVENT_HAS_RESERVATIONS"
    assert await db.events.count_documents({}) == 1


async def test_delete_unknown_event(client: AsyncClient, db: Db) -> None:
    headers = await headers_for(client, db, "admin")

    response = await client.delete(f"/events/{ObjectId()}", headers=headers)

    assert response.status_code == 404
