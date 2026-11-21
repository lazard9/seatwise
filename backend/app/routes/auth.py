from typing import Annotated

from fastapi import APIRouter, Cookie, Response, status

from app.auth.cookies import REFRESH_COOKIE, clear_refresh_cookie, set_refresh_cookie
from app.auth.dependencies import AppSettings, CurrentUser
from app.auth.tokens import create_access_token
from app.database.dependencies import Database
from app.errors import Unauthorized, error_response
from app.models.auth import LoginRequest, TokenResponse
from app.models.users import UserCreate, UserPublic
from app.services import auth as auth_service
from app.services import sessions
from app.services.users import UserDoc, serialize_user

router = APIRouter(prefix="/auth", tags=["auth"])

RefreshCookie = Annotated[str | None, Cookie(alias=REFRESH_COOKIE)]


def _token_response(user: UserDoc, settings: AppSettings) -> TokenResponse:
    token, expires_in = create_access_token(str(user["_id"]), settings)
    return TokenResponse(access_token=token, expires_in=expires_in, user=serialize_user(user))


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: Database) -> UserPublic:
    user = await auth_service.register(db.users, data)
    return serialize_user(user)


@router.post("/login")
async def login(
    data: LoginRequest, response: Response, db: Database, settings: AppSettings
) -> TokenResponse:
    user = await auth_service.authenticate(db.users, data.email, data.password)
    refresh_token = await sessions.start_session(db, user["_id"], settings)
    set_refresh_cookie(response, refresh_token, settings)
    return _token_response(user, settings)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={401: {"description": "No, invalid, expired, revoked or reused refresh token"}},
)
async def refresh(
    response: Response, db: Database, settings: AppSettings, refresh_token: RefreshCookie = None
) -> TokenResponse | Response:
    """Rotate the refresh cookie and return a new access token."""
    try:
        if refresh_token is None:
            raise Unauthorized("Not signed in", code="NOT_AUTHENTICATED")
        user, new_token = await sessions.rotate(db, refresh_token, settings)
    except Unauthorized as exc:
        # The cookie is dead, so stop the browser from sending it.
        failed = error_response(exc)
        clear_refresh_cookie(failed, settings)
        return failed
    set_refresh_cookie(response, new_token, settings)
    return _token_response(user, settings)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response, db: Database, settings: AppSettings, refresh_token: RefreshCookie = None
) -> None:
    """End this session only. Works without an access token, which may have expired."""
    if refresh_token is not None:
        await sessions.end_session(db, refresh_token)
    clear_refresh_cookie(response, settings)


@router.get("/me")
async def me(user: CurrentUser) -> UserPublic:
    return serialize_user(user)
