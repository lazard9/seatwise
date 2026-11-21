from app.auth.passwords import hash_password, needs_rehash, verify_password
from app.errors import Unauthorized
from app.models.users import Role, UserCreate
from app.services.users import UserDoc, Users, create_user, find_user_by_email

# Verified when the email is unknown, so a missing account takes as long as a
# wrong password and response times do not reveal which emails are registered.
_DUMMY_HASH = hash_password("dummy-password-for-timing")

INVALID_CREDENTIALS = "Email or password is incorrect"


async def register(users: Users, data: UserCreate) -> UserDoc:
    """New accounts are always attendees; the role is never taken from the request."""
    return await create_user(users, data, role=Role.ATTENDEE)


async def authenticate(users: Users, email: str, password: str) -> UserDoc:
    user = await find_user_by_email(users, email)
    if user is None:
        verify_password(_DUMMY_HASH, password)
        raise Unauthorized(INVALID_CREDENTIALS, code="INVALID_CREDENTIALS")
    if not verify_password(user["password_hash"], password):
        raise Unauthorized(INVALID_CREDENTIALS, code="INVALID_CREDENTIALS")

    if needs_rehash(user["password_hash"]):
        new_hash = hash_password(password)
        await users.update_one({"_id": user["_id"]}, {"$set": {"password_hash": new_hash}})
        user["password_hash"] = new_hash
    return user
