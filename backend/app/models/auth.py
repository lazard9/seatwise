from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.models.users import PASSWORD_MAX_LENGTH, UserPublic


class LoginRequest(BaseModel):
    # Not EmailStr: a malformed email is just a failed login, not a 422 that
    # tells the caller which part was wrong.
    email: Annotated[str, Field(min_length=1, max_length=320)]
    password: Annotated[str, Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)]


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"  # noqa: S105  # OAuth2 scheme name
    expires_in: int
    user: UserPublic
