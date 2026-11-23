import re
from datetime import datetime
from enum import StrEnum
from typing import Any

from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from app.database.transactions import run_in_transaction
from app.errors import BadRequest, Conflict, Forbidden, NotFound, Unprocessable
from app.ids import parse_object_id
from app.models.events import Category, EventPublic, EventStatus, EventWrite
from app.models.users import Role
from app.services.users import UserDoc
from app.utils.slugs import slugify
from app.utils.time import utcnow

type EventDoc = dict[str, Any]
type Events = AsyncCollection[EventDoc]
type Db = AsyncDatabase[dict[str, Any]]

# Two creates with the same title can pick the same slug; the loser retries with the next one.
SLUG_ATTEMPTS = 10


def is_past(doc: EventDoc, now: datetime | None = None) -> bool:
    """An event is past once it has ended. A running event is not past."""
    return doc["ends_at"] <= (now or utcnow())


def serialize_event(doc: EventDoc, now: datetime | None = None) -> EventPublic:
    """The only way an event leaves the service layer. `image_public_id` is never included."""
    return EventPublic(
        id=str(doc["_id"]),
        title=doc["title"],
        slug=doc["slug"],
        description=doc["description"],
        category=Category(doc["category"]),
        city=doc["city"],
        venue=doc["venue"],
        address=doc.get("address"),
        starts_at=doc["starts_at"],
        ends_at=doc["ends_at"],
        capacity=doc["capacity"],
        seats_taken=doc["seats_taken"],
        seats_left=max(doc["capacity"] - doc["seats_taken"], 0),
        price=doc["price"],
        image=doc.get("image"),
        status=EventStatus(doc["status"]),
        organizer_id=str(doc["organizer_id"]),
        rating_avg=doc["rating_avg"],
        rating_count=doc["rating_count"],
        is_past=is_past(doc, now),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


def _is_admin(user: UserDoc | None) -> bool:
    return user is not None and user["role"] == Role.ADMIN.value


def _is_owner(doc: EventDoc, user: UserDoc | None) -> bool:
    return user is not None and doc["organizer_id"] == user["_id"]


def can_see(doc: EventDoc, user: UserDoc | None) -> bool:
    """Published and cancelled events are public, so a link to a cancelled event says so.
    Drafts: their organizer and admins."""
    return doc["status"] != EventStatus.DRAFT.value or _is_admin(user) or _is_owner(doc, user)


def _not_found() -> NotFound:
    return NotFound("Event not found", code="EVENT_NOT_FOUND")


# Create


async def _free_slug(events: Events, base: str) -> str:
    """`base` if nobody has it, otherwise `base-2`, `base-3` and so on."""
    pattern = f"^{re.escape(base)}(-[0-9]+)?$"
    taken = {doc["slug"] async for doc in events.find({"slug": {"$regex": pattern}}, {"slug": 1})}
    if base not in taken:
        return base
    number = 2
    while f"{base}-{number}" in taken:
        number += 1
    return f"{base}-{number}"


async def create_event(events: Events, data: EventWrite, organizer: UserDoc) -> EventDoc:
    """Create a draft owned by the caller. The slug comes from the title and never changes."""
    now = utcnow()
    if data.starts_at <= now:
        raise Unprocessable("The event must start in the future", code="STARTS_IN_PAST")

    doc: EventDoc = {
        **data.model_dump(),
        "category": data.category.value,
        "seats_taken": 0,
        "image": None,
        "status": EventStatus.DRAFT.value,
        "organizer_id": organizer["_id"],
        "rating_avg": 0.0,
        "rating_count": 0,
        "created_at": now,
        "updated_at": now,
    }
    base = slugify(data.title)
    for _ in range(SLUG_ATTEMPTS):
        doc["slug"] = await _free_slug(events, base)
        doc.pop("_id", None)
        try:
            result = await events.insert_one(doc)
        except DuplicateKeyError:
            # The unique index decides: another create took this slug first.
            continue
        doc["_id"] = result.inserted_id
        return doc
    raise Conflict("Could not pick a free link for this title", code="SLUG_UNAVAILABLE")


# Read


async def get_event(events: Events, event_id: str, user: UserDoc | None) -> EventDoc:
    doc = await events.find_one({"_id": parse_object_id(event_id, what="event id")})
    # A hidden event answers like a missing one, so its existence does not leak.
    if doc is None or not can_see(doc, user):
        raise _not_found()
    return doc


async def get_event_by_slug(events: Events, slug: str, user: UserDoc | None) -> EventDoc:
    doc = await events.find_one({"slug": slug})
    if doc is None or not can_see(doc, user):
        raise _not_found()
    return doc


# Change


async def _get_for_change(events: Events, event_id: str, user: UserDoc) -> EventDoc:
    """The event when `user` may change it: an admin, or its organizer before it has ended."""
    doc = await get_event(events, event_id, user)
    if not (_is_admin(user) or _is_owner(doc, user)):
        raise Forbidden("Only the organizer of this event can change it", code="NOT_EVENT_OWNER")
    if not _is_admin(user) and is_past(doc):
        raise Forbidden("This event has ended and can no longer be changed", code="EVENT_PAST")
    return doc


async def update_event(events: Events, event_id: str, data: EventWrite, user: UserDoc) -> EventDoc:
    """Replace the editable fields. The slug, status, seats and ratings stay as they are."""
    doc = await _get_for_change(events, event_id, user)
    if doc["status"] == EventStatus.CANCELLED.value:
        raise Conflict("A cancelled event cannot be edited", code="EVENT_CANCELLED")

    changes = {**data.model_dump(), "category": data.category.value, "updated_at": utcnow()}
    # The conditions are checked by the write itself, so a reservation or a cancel that
    # lands between the read above and this update cannot be overwritten.
    updated = await events.find_one_and_update(
        {
            "_id": doc["_id"],
            "status": {"$ne": EventStatus.CANCELLED.value},
            "seats_taken": {"$lte": data.capacity},
        },
        {"$set": changes},
        return_document=ReturnDocument.AFTER,
    )
    if updated is not None:
        return updated

    current = await events.find_one({"_id": doc["_id"]})
    if current is None:
        raise _not_found()
    if current["status"] == EventStatus.CANCELLED.value:
        raise Conflict("A cancelled event cannot be edited", code="EVENT_CANCELLED")
    raise Conflict(
        f"Capacity cannot be lower than the {current['seats_taken']} seats already taken",
        code="CAPACITY_BELOW_SEATS_TAKEN",
    )


async def publish_event(events: Events, event_id: str, user: UserDoc) -> EventDoc:
    """Draft to published. Any other starting state is an invalid transition."""
    doc = await _get_for_change(events, event_id, user)
    updated = await events.find_one_and_update(
        {"_id": doc["_id"], "status": EventStatus.DRAFT.value},
        {"$set": {"status": EventStatus.PUBLISHED.value, "updated_at": utcnow()}},
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        raise BadRequest("Only a draft can be published", code="INVALID_TRANSITION")
    return updated


async def cancel_event(db: Db, event_id: str, user: UserDoc) -> EventDoc:
    """Cancel the event and all its confirmed reservations in one transaction.

    Seats are not released: the event is not happening, so nobody can reserve them.
    """
    doc = await _get_for_change(db.events, event_id, user)

    async def cancel(session: AsyncClientSession) -> EventDoc | None:
        now = utcnow()
        event = await db.events.find_one_and_update(
            {"_id": doc["_id"], "status": {"$ne": EventStatus.CANCELLED.value}},
            {"$set": {"status": EventStatus.CANCELLED.value, "updated_at": now}},
            return_document=ReturnDocument.AFTER,
            session=session,
        )
        if event is None:
            return None
        await db.reservations.update_many(
            {"event_id": doc["_id"], "status": "confirmed"},
            {"$set": {"status": "cancelled", "cancelled_at": now, "cancelled_by": "organizer"}},
            session=session,
        )
        return event

    cancelled = await run_in_transaction(db, cancel)
    if cancelled is None:
        raise BadRequest("This event is already cancelled", code="INVALID_TRANSITION")
    return cancelled


class _DeleteOutcome(StrEnum):
    DELETED = "deleted"
    MISSING = "missing"
    HAS_RESERVATIONS = "has_reservations"


async def delete_event(db: Db, event_id: str) -> None:
    """Delete an event that never had a reservation. Callers check the admin role."""
    oid: ObjectId = parse_object_id(event_id, what="event id")

    async def delete(session: AsyncClientSession) -> _DeleteOutcome:
        # Read inside the transaction: a reservation commit also writes the event,
        # so it conflicts with this delete and one of the two is retried.
        if await db.events.find_one({"_id": oid}, {"_id": 1}, session=session) is None:
            return _DeleteOutcome.MISSING
        if await db.reservations.find_one({"event_id": oid}, {"_id": 1}, session=session):
            return _DeleteOutcome.HAS_RESERVATIONS
        await db.events.delete_one({"_id": oid}, session=session)
        return _DeleteOutcome.DELETED

    outcome = await run_in_transaction(db, delete)
    if outcome is _DeleteOutcome.MISSING:
        raise _not_found()
    if outcome is _DeleteOutcome.HAS_RESERVATIONS:
        raise Conflict(
            "An event with reservations cannot be deleted; cancel it instead",
            code="EVENT_HAS_RESERVATIONS",
        )
