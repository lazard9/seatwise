from typing import ClassVar

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class DomainError(Exception):
    """A business rule or lookup failed. Services raise these; they know nothing about HTTP.

    The single handler below turns them into `{"detail": ..., "code": ...}` with
    the status of the subclass. The frontend branches on `code`.
    """

    status_code: ClassVar[int] = status.HTTP_400_BAD_REQUEST
    default_code: ClassVar[str] = "BAD_REQUEST"

    def __init__(self, detail: str, code: str | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.code = code or self.default_code


class BadRequest(DomainError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "BAD_REQUEST"


class Unauthorized(DomainError):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_code = "UNAUTHORIZED"


class Forbidden(DomainError):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "FORBIDDEN"


class NotFound(DomainError):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = "NOT_FOUND"


class Conflict(DomainError):
    status_code = status.HTTP_409_CONFLICT
    default_code = "CONFLICT"


async def domain_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    # Registered for DomainError only; the signature is Starlette's generic one.
    if not isinstance(exc, DomainError):
        raise exc
    headers = {"WWW-Authenticate": "Bearer"} if isinstance(exc, Unauthorized) else None
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.code},
        headers=headers,
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, domain_error_handler)
