from datetime import timedelta

import jwt

from app.config import Settings
from app.errors import Unauthorized
from app.utils.time import utcnow

ALGORITHM = "HS256"
ACCESS_TOKEN_TYPE = "access"  # noqa: S105  # a claim value, not a secret


def create_access_token(user_id: str, settings: Settings) -> tuple[str, int]:
    """Return a signed access token and its lifetime in seconds.

    The token carries only the user id. The role is read from the database on
    every request, so a role change applies at once.
    """
    lifetime = timedelta(minutes=settings.access_token_expire_minutes)
    now = utcnow()
    claims = {"sub": user_id, "type": ACCESS_TOKEN_TYPE, "iat": now, "exp": now + lifetime}
    token = jwt.encode(claims, settings.jwt_secret, algorithm=ALGORITHM)
    return token, int(lifetime.total_seconds())


def decode_access_token(token: str, settings: Settings) -> str:
    """Return the user id from a valid access token, or raise Unauthorized."""
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[ALGORITHM],
            options={"require": ["sub", "exp", "iat", "type"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise Unauthorized("Access token has expired", code="TOKEN_EXPIRED") from exc
    except jwt.InvalidTokenError as exc:
        raise Unauthorized("Invalid access token", code="INVALID_TOKEN") from exc

    if claims["type"] != ACCESS_TOKEN_TYPE or not isinstance(claims["sub"], str):
        raise Unauthorized("Invalid access token", code="INVALID_TOKEN")
    return claims["sub"]
