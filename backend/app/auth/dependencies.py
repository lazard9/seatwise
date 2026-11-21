from collections.abc import Awaitable, Callable
from typing import Annotated

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.tokens import decode_access_token
from app.config import Settings
from app.database.dependencies import Database
from app.errors import Forbidden, Unauthorized
from app.models.users import Role
from app.services.users import UserDoc

# auto_error=False: a missing header is reported in our own error shape below.
_bearer = HTTPBearer(auto_error=False)
Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]


def get_settings_from_app(request: Request) -> Settings:
    return request.app.state.settings


AppSettings = Annotated[Settings, Depends(get_settings_from_app)]


async def _user_from_token(token: str, db: Database, settings: Settings) -> UserDoc:
    user_id = decode_access_token(token, settings)
    try:
        oid = ObjectId(user_id)
    except InvalidId as exc:
        raise Unauthorized("Invalid access token", code="INVALID_TOKEN") from exc
    # The role comes from this read, never from the token.
    user = await db.users.find_one({"_id": oid})
    if user is None:
        raise Unauthorized("Account no longer exists", code="INVALID_TOKEN")
    return user


async def get_current_user(
    credentials: Credentials, db: Database, settings: AppSettings
) -> UserDoc:
    if credentials is None:
        raise Unauthorized("Not authenticated", code="NOT_AUTHENTICATED")
    return await _user_from_token(credentials.credentials, db, settings)


async def get_optional_user(
    credentials: Credentials, db: Database, settings: AppSettings
) -> UserDoc | None:
    """The caller when signed in, None for guests. A bad token is still an error."""
    if credentials is None:
        return None
    return await _user_from_token(credentials.credentials, db, settings)


CurrentUser = Annotated[UserDoc, Depends(get_current_user)]
OptionalUser = Annotated[UserDoc | None, Depends(get_optional_user)]


def require_roles(*roles: Role) -> Callable[..., Awaitable[UserDoc]]:
    allowed = {role.value for role in roles}

    async def dependency(user: CurrentUser) -> UserDoc:
        if user["role"] not in allowed:
            raise Forbidden("You do not have permission to do this", code="FORBIDDEN_ROLE")
        return user

    return dependency


AdminUser = Annotated[UserDoc, Depends(require_roles(Role.ADMIN))]
