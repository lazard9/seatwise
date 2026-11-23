import re
from typing import Any

from pymongo import DESCENDING, ReturnDocument
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.errors import DuplicateKeyError

from app.auth.passwords import hash_password
from app.errors import Conflict, Forbidden, NotFound
from app.ids import parse_object_id
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


async def list_users(
    users: Users,
    page: int,
    page_size: int,
    role: Role | None = None,
    search: str | None = None,
) -> tuple[list[UserDoc], int]:
    """Users newest first, with the total that matches. `search` matches email or display name."""
    query: dict[str, Any] = {}
    if role is not None:
        query["role"] = role.value
    if search:
        # Escaped, so the text is matched literally and cannot be a costly pattern.
        pattern = {"$regex": re.escape(search.strip()), "$options": "i"}
        query["$or"] = [{"email": pattern}, {"display_name": pattern}]

    total = await users.count_documents(query)
    cursor = (
        users.find(query)
        .sort([("created_at", DESCENDING), ("_id", DESCENDING)])
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    return await cursor.to_list(), total


async def change_role(users: Users, user_id: str, role: Role, acting_admin: UserDoc) -> UserDoc:
    """Set another user's role. An admin cannot change their own, so one admin always remains."""
    oid = parse_object_id(user_id, what="user id")
    if oid == acting_admin["_id"]:
        raise Forbidden("You cannot change your own role", code="CANNOT_CHANGE_OWN_ROLE")

    updated = await users.find_one_and_update(
        {"_id": oid}, {"$set": {"role": role.value}}, return_document=ReturnDocument.AFTER
    )
    if updated is None:
        raise NotFound("User not found", code="USER_NOT_FOUND")
    return updated
