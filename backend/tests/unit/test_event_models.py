from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from app.models.events import EventWrite


def valid(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "title": "Jazz Night",
        "description": "Live jazz.",
        "category": "music",
        "city": "Novi Sad",
        "venue": "Club",
        "starts_at": "2030-05-01T20:00:00+02:00",
        "ends_at": "2030-05-01T23:00:00+02:00",
        "capacity": 100,
    }
    data.update(overrides)
    return data


def test_valid_event_defaults_and_utc() -> None:
    event = EventWrite(**valid())

    assert event.price == 0
    assert event.address is None
    assert event.starts_at == datetime(2030, 5, 1, 18, 0, tzinfo=UTC)
    assert event.starts_at.tzinfo == UTC


@pytest.mark.parametrize(
    "overrides",
    [
        {"title": "ab"},
        {"title": "x" * 121},
        {"description": "   "},
        {"category": "opera"},
        {"city": ""},
        {"venue": ""},
        {"capacity": 0},
        {"price": -1},
        {"starts_at": "2030-05-01T20:00:00"},
        {"ends_at": "2030-05-01T20:00:00+02:00"},
        {"ends_at": "2030-05-01T19:00:00+02:00"},
    ],
)
def test_invalid_fields_are_rejected(overrides: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        EventWrite(**valid(**overrides))


def test_blank_address_is_none_and_text_is_trimmed() -> None:
    event = EventWrite(**valid(address="  ", title="  Jazz Night  "))

    assert event.address is None
    assert event.title == "Jazz Night"


def test_price_is_rounded_to_cents() -> None:
    assert EventWrite(**valid(price=12.3456)).price == 12.35
