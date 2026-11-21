from fastapi import Response

from app.config import Settings

REFRESH_COOKIE = "seatwise_refresh"
# Sent only to the auth routes, never with ordinary API calls.
REFRESH_COOKIE_PATH = "/auth"


def set_refresh_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        REFRESH_COOKIE,
        token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite="lax",
    )


def clear_refresh_cookie(response: Response, settings: Settings) -> None:
    # Same attributes as when set, or some browsers keep the old cookie.
    response.delete_cookie(
        REFRESH_COOKIE,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite="lax",
    )
