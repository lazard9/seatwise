from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Self

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    BeforeValidator,
    Field,
    StringConstraints,
    model_validator,
)

TITLE_MIN_LENGTH = 3
TITLE_MAX_LENGTH = 120
DESCRIPTION_MAX_LENGTH = 5000
CAPACITY_MAX = 100_000
PRICE_MAX = 1_000_000


class Category(StrEnum):
    MUSIC = "music"
    THEATRE = "theatre"
    TALK = "talk"
    WORKSHOP = "workshop"
    SPORT = "sport"
    FESTIVAL = "festival"
    OTHER = "other"


class EventStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"


def _to_utc(value: datetime) -> datetime:
    return value.astimezone(UTC)


def _blank_to_none(value: object) -> object:
    # Forms send "" for an empty optional field; store it as missing.
    if isinstance(value, str) and not value.strip():
        return None
    return value


def _round_price(value: float) -> float:
    return round(value, 2)


Title = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, min_length=TITLE_MIN_LENGTH, max_length=TITLE_MAX_LENGTH
    ),
]
Description = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=DESCRIPTION_MAX_LENGTH)
]
City = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
Venue = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
AddressText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Address = Annotated[AddressText | None, BeforeValidator(_blank_to_none)]
# A time without an offset is ambiguous, so it is rejected instead of guessed.
UtcDatetime = Annotated[AwareDatetime, AfterValidator(_to_utc)]
Capacity = Annotated[int, Field(ge=1, le=CAPACITY_MAX)]
Price = Annotated[float, Field(ge=0, le=PRICE_MAX), AfterValidator(_round_price)]


class EventWrite(BaseModel):
    """Fields an organizer sets, on create and on edit. Everything else is the backend's."""

    title: Title
    description: Description
    category: Category
    city: City
    venue: Venue
    address: Address = None
    starts_at: UtcDatetime
    ends_at: UtcDatetime
    capacity: Capacity
    price: Price = 0

    @model_validator(mode="after")
    def _ends_after_start(self) -> Self:
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class EventPublic(BaseModel):
    id: str
    title: str
    slug: str
    description: str
    category: Category
    city: str
    venue: str
    address: str | None
    starts_at: datetime
    ends_at: datetime
    capacity: int
    seats_taken: int
    seats_left: int
    price: float
    image: str | None
    status: EventStatus
    organizer_id: str
    rating_avg: float
    rating_count: int
    is_past: bool
    created_at: datetime
    updated_at: datetime
