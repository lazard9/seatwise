"""GET /events, /events/cities and /events/tags: filters, sorts, pages, the archive and `mine`."""

from datetime import datetime, timedelta
from typing import Any

import pytest
from bson import ObjectId
from httpx import AsyncClient
from pymongo.asynchronous.database import AsyncDatabase

from app.models.users import Role
from app.utils.time import utcnow
from tests.helpers import bearer, login, make_user

type Db = AsyncDatabase[dict[str, Any]]

NOW = utcnow()


async def put_event(db: Db, title: str, *, days: float = 10, **fields: Any) -> dict[str, Any]:
    """Insert a published event starting `days` from now, lasting two hours."""
    starts: datetime = NOW + timedelta(days=days)
    doc: dict[str, Any] = {
        "title": title,
        "slug": f"{title.lower().replace(' ', '-')}-{ObjectId()}",
        "description": f"<p>About {title}</p>",
        "description_text": f"About {title}",
        "category": "music",
        "city": "Novi Sad",
        "venue": "Hall",
        "address": None,
        "starts_at": starts,
        "ends_at": starts + timedelta(hours=2),
        "capacity": 100,
        "seats_taken": 0,
        "price": 1000.0,
        "tags": [],
        "participants": [],
        "image": None,
        "status": "published",
        "organizer_id": ObjectId(),
        "organizer_name": "Org",
        "rating_avg": 0.0,
        "rating_count": 0,
        "created_at": NOW,
        "updated_at": NOW,
    }
    doc.update(fields)
    await db.events.insert_one(doc)
    return doc


async def titles(client: AsyncClient, params: dict[str, Any] | None = None, **kw: Any) -> list[str]:
    response = await client.get("/events", params=params or {}, **kw)
    assert response.status_code == 200, response.text
    return [item["title"] for item in response.json()["items"]]


# What is listed


async def test_default_lists_published_upcoming_events_soonest_first(
    client: AsyncClient, db: Db
) -> None:
    await put_event(db, "Later", days=5)
    await put_event(db, "Sooner", days=1)
    # Started an hour ago, ends in an hour: still upcoming.
    await put_event(
        db, "Running", starts_at=NOW - timedelta(hours=1), ends_at=NOW + timedelta(hours=1)
    )
    await put_event(db, "Draft", status="draft")
    await put_event(db, "Cancelled", status="cancelled")
    await put_event(db, "Ended", days=-1)

    response = await client.get("/events")

    body = response.json()
    assert [item["title"] for item in body["items"]] == ["Running", "Sooner", "Later"]
    assert (body["total"], body["page"], body["page_size"]) == (3, 1, 20)
    assert body["items"][0]["organizer_name"] == "Org"
    assert "description_text" not in body["items"][0]


async def test_past_lists_ended_events_latest_first(client: AsyncClient, db: Db) -> None:
    await put_event(db, "Long ago", days=-30)
    await put_event(db, "Yesterday", days=-1)
    await put_event(db, "Upcoming", days=1)
    await put_event(db, "Old draft", days=-2, status="draft")

    assert await titles(client, {"when": "past"}) == ["Yesterday", "Long ago"]


# Filters: each one keeps what matches and drops what does not


@pytest.mark.parametrize(
    ("params", "fields_in", "fields_out"),
    [
        ({"category": "theatre"}, {"category": "theatre"}, {"category": "music"}),
        ({"tag": "  JAZZ "}, {"tags": ["jazz", "live"]}, {"tags": ["rock"]}),
        ({"city": "Beograd"}, {"city": "Beograd"}, {"city": "Novi Sad"}),
        (
            {"person": "djordje-balasevic"},
            {"participants": [{"name": "Đorđe", "role": None, "key": "djordje-balasevic"}]},
            {"participants": [{"name": "Ana", "role": None, "key": "ana"}]},
        ),
        ({"free": "true"}, {"price": 0.0}, {"price": 10.0}),
        ({"min_price": 500}, {"price": 500.0}, {"price": 499.0}),
        ({"max_price": 500}, {"price": 500.0}, {"price": 501.0}),
        ({"has_seats": "true"}, {"seats_taken": 99}, {"seats_taken": 100}),
    ],
)
async def test_filter(
    client: AsyncClient,
    db: Db,
    params: dict[str, Any],
    fields_in: dict[str, Any],
    fields_out: dict[str, Any],
) -> None:
    await put_event(db, "Match", **fields_in)
    await put_event(db, "Other", **fields_out)

    assert await titles(client, params) == ["Match"]


async def test_filter_by_organizer(client: AsyncClient, db: Db) -> None:
    organizer = ObjectId()
    await put_event(db, "Theirs", organizer_id=organizer)
    await put_event(db, "Someone else's")

    assert await titles(client, {"organizer": str(organizer)}) == ["Theirs"]
    bad = await client.get("/events", params={"organizer": "nope"})
    assert bad.status_code == 400
    assert bad.json()["code"] == "INVALID_ID"


async def test_date_range_keeps_events_that_overlap_it(client: AsyncClient, db: Db) -> None:
    day = NOW + timedelta(days=10)
    await put_event(
        db, "Inside", starts_at=day + timedelta(hours=10), ends_at=day + timedelta(hours=12)
    )
    # A festival that began before the range and is still on when it starts.
    await put_event(
        db, "Festival", starts_at=day - timedelta(days=2), ends_at=day + timedelta(hours=1)
    )
    await put_event(
        db, "Before", starts_at=day - timedelta(days=2), ends_at=day - timedelta(days=1)
    )
    await put_event(db, "After", starts_at=day + timedelta(days=2), ends_at=day + timedelta(days=3))
    params = {"date_from": day.isoformat(), "date_to": (day + timedelta(days=1)).isoformat()}

    assert await titles(client, params) == ["Festival", "Inside"]


@pytest.mark.parametrize(
    ("search", "fields"),
    [
        ("jazz", {"title": "Big JAZZ night"}),
        ("garden", {"venue": "The Garden"}),
        ("kragujevac", {"city": "Kragujevac"}),
        ("trumpet", {"description_text": "A trumpet solo"}),
        ("open air", {"tags": ["open air"]}),
        ("balašević", {"participants": [{"name": "Đorđe Balašević", "role": None, "key": "x"}]}),
    ],
)
async def test_search_looks_in_each_field(
    client: AsyncClient, db: Db, search: str, fields: dict[str, Any]
) -> None:
    await put_event(db, fields.pop("title", "Match"), **fields)
    await put_event(db, "Other")

    assert len(await titles(client, {"search": search})) == 1


async def test_search_matches_text_not_markup_or_patterns(client: AsyncClient, db: Db) -> None:
    await put_event(
        db, "Styled", description="<p><strong>Bold</strong></p>", description_text="Bold"
    )
    await put_event(db, "Dotted a.b")
    await put_event(db, "Axb")

    assert await titles(client, {"search": "strong"}) == []
    assert await titles(client, {"search": "a.b"}) == ["Dotted a.b"]


# Sorts


@pytest.mark.parametrize(
    ("sort", "expected"),
    [
        ("soonest", ["A", "B", "C"]),
        ("latest", ["C", "B", "A"]),
        ("newest", ["B", "C", "A"]),
        ("price_asc", ["C", "A", "B"]),
        ("price_desc", ["B", "A", "C"]),
        ("rating_desc", ["A", "C", "B"]),
    ],
)
async def test_sort(client: AsyncClient, db: Db, sort: str, expected: list[str]) -> None:
    await put_event(
        db, "A", days=1, price=500.0, rating_avg=4.5, created_at=NOW - timedelta(days=3)
    )
    await put_event(db, "B", days=2, price=900.0, rating_avg=3.0, created_at=NOW)
    await put_event(db, "C", days=3, price=0.0, rating_avg=4.5, created_at=NOW - timedelta(days=1))

    assert await titles(client, {"sort": sort}) == expected


async def test_equal_start_times_keep_one_order_across_pages(client: AsyncClient, db: Db) -> None:
    starts = NOW + timedelta(days=3)
    for n in range(7):
        await put_event(db, f"Same {n}", starts_at=starts, ends_at=starts + timedelta(hours=1))

    seen: list[str] = []
    for page in (1, 2, 3, 4):
        seen += await titles(client, {"page": page, "page_size": 2})

    assert sorted(seen) == [f"Same {n}" for n in range(7)]
    assert len(seen) == len(set(seen)) == 7


async def test_pages(client: AsyncClient, db: Db) -> None:
    for n in range(5):
        await put_event(db, f"E{n}", days=n + 1)

    response = await client.get("/events", params={"page": 2, "page_size": 2})

    body = response.json()
    assert [item["title"] for item in body["items"]] == ["E2", "E3"]
    assert (body["total"], body["page"], body["page_size"]) == (5, 2, 2)


@pytest.mark.parametrize(
    "params",
    [
        {"page": 0},
        {"page_size": 101},
        {"sort": "random"},
        {"when": "always"},
        {"category": "opera"},
        {"min_price": -1},
        {"date_from": "2030-01-01T00:00:00"},
    ],
)
async def test_invalid_parameters_are_422(client: AsyncClient, params: dict[str, Any]) -> None:
    response = await client.get("/events", params=params)

    assert response.status_code == 422


# mine: the caller's own events, drafts and cancelled included


async def test_mine_needs_sign_in(client: AsyncClient) -> None:
    response = await client.get("/events", params={"mine": "true"})

    assert response.status_code == 401


@pytest.mark.parametrize("role", [Role.ADMIN, Role.ORGANIZER, Role.ATTENDEE])
async def test_mine_lists_own_events_in_every_status(
    client: AsyncClient, db: Db, role: Role
) -> None:
    user = await make_user(db, email="me@example.com", role=role)
    token = await login(client, "me@example.com")
    await put_event(db, "Mine draft", days=1, status="draft", organizer_id=user["_id"])
    await put_event(db, "Mine cancelled", days=2, status="cancelled", organizer_id=user["_id"])
    await put_event(db, "Mine published", days=3, organizer_id=user["_id"])
    await put_event(db, "Not mine")

    listed = await titles(client, {"mine": "true"}, headers=bearer(token))

    # An attendee cannot create events, so in practice their list is empty.
    assert listed == ["Mine draft", "Mine cancelled", "Mine published"]


# Cities and tags for the filters


async def test_cities_of_published_events_in_alphabetical_order(
    client: AsyncClient, db: Db
) -> None:
    await put_event(db, "1", city="Novi Sad")
    await put_event(db, "2", city="beograd")
    await put_event(db, "3", city="Čačak", days=-5)
    await put_event(db, "4", city="Novi Sad")
    await put_event(db, "5", city="Secret", status="draft")

    response = await client.get("/events/cities")

    # Č sorts with C, as in the Serbian alphabet, not after Z.
    assert response.json() == ["beograd", "Čačak", "Novi Sad"]


async def test_tags_most_used_first(client: AsyncClient, db: Db) -> None:
    await put_event(db, "1", tags=["jazz", "live"])
    await put_event(db, "2", tags=["jazz", "blues"])
    await put_event(db, "3", tags=["jazz", "live"])
    await put_event(db, "4", tags=["hidden"], status="draft")

    everything = await client.get("/events/tags")
    top_two = await client.get("/events/tags", params={"limit": 2})

    assert everything.json() == ["jazz", "live", "blues"]
    assert top_two.json() == ["jazz", "live"]


async def test_created_event_carries_the_organizer_name(client: AsyncClient, db: Db) -> None:
    await make_user(db, email="org@example.com", role=Role.ORGANIZER, display_name="Marko")
    token = await login(client, "org@example.com")
    starts = NOW + timedelta(days=5)
    body = {
        "title": "Named",
        "description": "<p>x</p>",
        "category": "talk",
        "city": "Niš",
        "venue": "Hall",
        "starts_at": starts.isoformat(),
        "ends_at": (starts + timedelta(hours=1)).isoformat(),
        "capacity": 10,
    }

    response = await client.post("/events", json=body, headers=bearer(token))

    assert response.json()["organizer_name"] == "Marko"
