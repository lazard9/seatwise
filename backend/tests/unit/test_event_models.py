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


def test_description_is_sanitized() -> None:
    event = EventWrite(**valid(description="<h2>Program</h2><p>Hi<script>x()</script></p>"))

    assert event.description == "<h2>Program</h2><p>Hi</p>"


@pytest.mark.parametrize("description", ["<p></p>", "<p> <br> </p>", "<script>x()</script>"])
def test_description_without_text_is_rejected(description: str) -> None:
    with pytest.raises(ValidationError):
        EventWrite(**valid(description=description))


def test_tags_are_normalized_and_deduplicated() -> None:
    event = EventWrite(**valid(tags=["  Jazz   Night ", "jazz night", "Džez"]))

    assert event.tags == ["jazz night", "džez"]


@pytest.mark.parametrize("tags", [["a"], ["x" * 31], [f"tag {n}" for n in range(11)], "jazz"])
def test_invalid_tags_are_rejected(tags: object) -> None:
    with pytest.raises(ValidationError):
        EventWrite(**valid(tags=tags))


def test_participants_trim_and_blank_role_is_none() -> None:
    event = EventWrite(
        **valid(
            participants=[
                {"name": " Ana Anić ", "role": " Director "},
                {"name": "Bajaga", "role": ""},
            ]
        )
    )

    assert [(p.name, p.role) for p in event.participants] == [
        ("Ana Anić", "Director"),
        ("Bajaga", None),
    ]


@pytest.mark.parametrize(
    "participants",
    [
        [{"name": "A"}],
        [{"name": "x" * 81}],
        [{"name": "Ana", "role": "x" * 41}],
        [{"name": f"Person {n}"} for n in range(21)],
    ],
)
def test_invalid_participants_are_rejected(participants: list[dict[str, str]]) -> None:
    with pytest.raises(ValidationError):
        EventWrite(**valid(participants=participants))


def test_new_fields_default_to_empty() -> None:
    event = EventWrite(**valid())

    assert event.tags == []
    assert event.participants == []
