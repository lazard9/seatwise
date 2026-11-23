from fastapi import APIRouter, status

from app.auth.dependencies import AdminUser, OptionalUser, OrganizerUser
from app.database.dependencies import Database
from app.models.events import EventPublic, EventWrite
from app.services import events as events_service
from app.services.events import serialize_event

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_event(data: EventWrite, user: OrganizerUser, db: Database) -> EventPublic:
    """Create a draft. The caller becomes its organizer."""
    return serialize_event(await events_service.create_event(db.events, data, user))


# Declared before /{event_id}, so "by-slug" is never read as an id.
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
