from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import AfterValidator, BaseModel, EmailStr, Field, StringConstraints

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


class Role(StrEnum):
    ADMIN = "admin"
    ORGANIZER = "organizer"
    ATTENDEE = "attendee"


def _lowercase(value: str) -> str:
    return value.lower()


# Emails are stored lowercased, so lookups and the unique index ignore case.
Email = Annotated[EmailStr, AfterValidator(_lowercase)]

DisplayName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=50)]

Password = Annotated[str, Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)]


class UserCreate(BaseModel):
    email: Email
    password: Password
    display_name: DisplayName


class UserPublic(BaseModel):
    id: str
    email: str
    display_name: str
    role: Role
    created_at: datetime
