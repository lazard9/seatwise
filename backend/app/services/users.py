from typing import Any

from pymongo.asynchronous.collection import AsyncCollection
from pymongo.errors import DuplicateKeyError

from app.auth.passwords import hash_password
from app.errors import Conflict
from app.models.users import Role, UserCreate, UserPublic
from app.utils.time import utcnow

type UserDoc = dict[str, Any]
type Users = AsyncCollection[UserDoc]


def serialize_user(doc: UserDoc) -> UserPublic:
    """The only way a user leaves the service layer. `password_hash` is never included."""
    return UserPublic(
        id=str(doc["_id"]),
        email=doc["email"],
        display_name=doc["display_name"],
        role=Role(doc["role"]),
        created_at=doc["created_at"],
    )


async def create_user(users: Users, data: UserCreate, role: Role = Role.ATTENDEE) -> UserDoc:
    doc: UserDoc = {
        "email": data.email,
        "password_hash": hash_password(data.password),
        "display_name": data.display_name,
        "role": role.value,
        "created_at": utcnow(),
    }
    try:
        result = await users.insert_one(doc)
    except DuplicateKeyError as exc:
        # The unique index decides, so two simultaneous sign-ups cannot both succeed.
        raise Conflict("An account with this email already exists", code="EMAIL_TAKEN") from exc
    doc["_id"] = result.inserted_id
    return doc


async def find_user_by_email(users: Users, email: str) -> UserDoc | None:
    return await users.find_one({"email": email.strip().lower()})
