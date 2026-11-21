from fastapi import APIRouter, status

from app.auth.dependencies import AppSettings, CurrentUser
from app.auth.tokens import create_access_token
from app.database.dependencies import Database
from app.models.auth import LoginRequest, TokenResponse
from app.models.users import UserCreate, UserPublic
from app.services import auth as auth_service
from app.services.users import serialize_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: Database) -> UserPublic:
    user = await auth_service.register(db.users, data)
    return serialize_user(user)


@router.post("/login")
async def login(data: LoginRequest, db: Database, settings: AppSettings) -> TokenResponse:
    user = await auth_service.authenticate(db.users, data.email, data.password)
    token, expires_in = create_access_token(str(user["_id"]), settings)
    return TokenResponse(access_token=token, expires_in=expires_in, user=serialize_user(user))


@router.get("/me")
async def me(user: CurrentUser) -> UserPublic:
    return serialize_user(user)
