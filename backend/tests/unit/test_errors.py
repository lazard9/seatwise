import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.errors import (
    BadRequest,
    Conflict,
    DomainError,
    Forbidden,
    NotFound,
    Unauthorized,
    register_error_handlers,
)
from app.ids import parse_object_id


def make_app(error: DomainError) -> FastAPI:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/boom")
    async def boom() -> None:
        raise error

    return app


@pytest.mark.parametrize(
    ("error", "status", "code"),
    [
        (BadRequest("Bad"), 400, "BAD_REQUEST"),
        (Unauthorized("Who are you"), 401, "UNAUTHORIZED"),
        (Forbidden("Not yours"), 403, "FORBIDDEN"),
        (NotFound("Gone"), 404, "NOT_FOUND"),
        (Conflict("Not enough seats", code="EVENT_FULL"), 409, "EVENT_FULL"),
    ],
)
async def test_domain_errors_map_to_status_and_stable_body(
    error: DomainError, status: int, code: str
) -> None:
    transport = ASGITransport(app=make_app(error))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/boom")

    assert response.status_code == status
    assert response.json() == {"detail": error.detail, "code": code}


async def test_unauthorized_sets_www_authenticate_header() -> None:
    transport = ASGITransport(app=make_app(Unauthorized("Missing token")))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/boom")

    assert response.headers["www-authenticate"] == "Bearer"


def test_parse_object_id_accepts_a_valid_id() -> None:
    assert str(parse_object_id("6740a1b2c3d4e5f6a7b8c9d0")) == "6740a1b2c3d4e5f6a7b8c9d0"


@pytest.mark.parametrize("value", ["", "abc", "6740a1b2c3d4e5f6a7b8c9dZ", "1" * 25])
def test_parse_object_id_rejects_malformed_ids(value: str) -> None:
    with pytest.raises(BadRequest) as info:
        parse_object_id(value, what="event id")

    assert info.value.code == "INVALID_ID"
    assert info.value.detail == "Invalid event id"
