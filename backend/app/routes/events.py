from typing import Annotated

from fastapi import APIRouter, Query, status

from app.auth.dependencies import AdminUser, OptionalUser, OrganizerUser
from app.database.dependencies import Database
from app.models.common import Page
from app.models.events import EventListQuery, EventPublic, EventWrite
from app.services import events as events_service
from app.services.events import serialize_event
from app.utils.time import utcnow

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_event(data: EventWrite, user: OrganizerUser, db: Database) -> EventPublic:
    """Create a draft. The caller becomes its organizer."""
    return serialize_event(await events_service.create_event(db.events, data, user))


@router.get("")
async def list_events(
    query: Annotated[EventListQuery, Query()], user: OptionalUser, db: Database
) -> Page[EventPublic]:
    """Published events, upcoming by default. With `mine=true`, the caller's own events in
    every status."""
    docs, total = await events_service.list_events(db.events, query, user)
    now = utcnow()
    return Page(
        items=[serialize_event(doc, now) for doc in docs],
        total=total,
        page=query.page,
        page_size=query.page_size,
    )


# The fixed paths below are declared before /{event_id}, so they are never read as an id.


@router.get("/cities")
async def list_cities(db: Database) -> list[str]:
    """Cities of published events, for the city filter."""
    return await events_service.list_cities(db.events)


@router.get("/tags")
async def popular_tags(db: Database, limit: Annotated[int, Query(ge=1, le=100)] = 50) -> list[str]:
    """Tags of published events, most used first, for filters and form suggestions."""
    return await events_service.popular_tags(db.events, limit)


@router.get("/by-slug/{slug}")
async def get_event_by_slug(slug: str, user: OptionalUser, db: Database) -> EventPublic:
    return serialize_event(await events_service.get_event_by_slug(db.events, slug, user))


@router.get("/{event_id}")
async def get_event(event_id: str, user: OptionalUser, db: Database) -> EventPublic:
    return serialize_event(await events_service.get_event(db.events, event_id, user))


@router.put("/{event_id}")
async def update_event(
    event_id: str, data: EventWrite, user: OrganizerUser, db: Database
) -> EventPublic:
    """Replace the editable fields. Organizer of the event or admin."""
    return serialize_event(await events_service.update_event(db.events, event_id, data, user))


@router.post("/{event_id}/publish")
async def publish_event(event_id: str, user: OrganizerUser, db: Database) -> EventPublic:
    return serialize_event(await events_service.publish_event(db.events, event_id, user))


@router.post("/{event_id}/cancel")
async def cancel_event(event_id: str, user: OrganizerUser, db: Database) -> EventPublic:
    """Cancel the event and its confirmed reservations."""
    return serialize_event(await events_service.cancel_event(db, event_id, user))


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: str, _admin: AdminUser, db: Database) -> None:
    """Admin only, and only for an event without reservations."""
    await events_service.delete_event(db, event_id)
