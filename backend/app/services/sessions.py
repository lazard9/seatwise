"""Refresh token sessions: rotation, reuse detection, and revocation.

Each sign-in starts a family. Every refresh marks the presented token as used
and issues the next one in the same family. A used token that comes back after
the grace period was copied, so the whole family is revoked.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

from bson import ObjectId
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.database import AsyncDatabase

from app.auth.tokens import hash_refresh_token, new_refresh_token
from app.config import Settings
from app.database.transactions import run_in_transaction
from app.errors import Unauthorized
from app.services.users import UserDoc
from app.utils.time import utcnow

type Db = AsyncDatabase[dict[str, Any]]

INVALID_REFRESH = "Session expired, please sign in again"


async def _insert_token(
    db: Db,
    user_id: ObjectId,
    family_id: ObjectId,
    settings: Settings,
    now: datetime,
    session: AsyncClientSession | None = None,
) -> str:
    token = new_refresh_token()
    await db.refresh_tokens.insert_one(
        {
            "token_hash": hash_refresh_token(token),
            "user_id": user_id,
            "family_id": family_id,
            "created_at": now,
            # Sliding: each refresh extends the session by the full lifetime.
            "expires_at": now + timedelta(days=settings.refresh_token_expire_days),
            "used_at": None,
            "revoked_at": None,
        },
        session=session,
    )
    return token


async def start_session(db: Db, user_id: ObjectId, settings: Settings) -> str:
    """Start a new family for a sign-in and return its first refresh token."""
    return await _insert_token(db, user_id, ObjectId(), settings, utcnow())


class _Outcome(StrEnum):
    ROTATED = "rotated"
    INVALID = "invalid"
    REUSED = "reused"


@dataclass(frozen=True)
class _Result:
    outcome: _Outcome
    user: UserDoc | None = None
    token: str | None = None
    family_id: ObjectId | None = None


async def rotate(db: Db, presented: str, settings: Settings) -> tuple[UserDoc, str]:
    """Exchange a refresh token for the next one. Return the user and the new token.

    Raises Unauthorized with INVALID_REFRESH_TOKEN for an unknown, expired or
    revoked token, and REFRESH_TOKEN_REUSED after revoking the family.
    """
    token_hash = hash_refresh_token(presented)
    grace = timedelta(seconds=settings.refresh_grace_seconds)

    async def attempt(session: AsyncClientSession) -> _Result:
        now = utcnow()
        doc = await db.refresh_tokens.find_one({"token_hash": token_hash}, session=session)
        if doc is None or doc["revoked_at"] is not None or doc["expires_at"] <= now:
            return _Result(_Outcome.INVALID)
        used_at = doc["used_at"]
        if used_at is not None and now - used_at > grace:
            return _Result(_Outcome.REUSED, family_id=doc["family_id"])

        user = await db.users.find_one({"_id": doc["user_id"]}, session=session)
        if user is None:
            return _Result(_Outcome.INVALID)

        # Always write the presented row, even inside the grace period. Two
        # rotations of one token, or a rotation racing a revocation, then touch
        # the same document and MongoDB lets only one of them commit; the
        # driver reruns the other, which then sees the new state.
        update: dict[str, Any] = {"last_used_at": now}
        if used_at is None:
            update["used_at"] = now
        await db.refresh_tokens.update_one(
            {"_id": doc["_id"], "revoked_at": None}, {"$set": update}, session=session
        )
        token = await _insert_token(
            db, doc["user_id"], doc["family_id"], settings, now, session=session
        )
        return _Result(_Outcome.ROTATED, user=user, token=token)

    result = await run_in_transaction(db, attempt)

    if result.outcome is _Outcome.REUSED and result.family_id is not None:
        await revoke_family(db, result.family_id)
        raise Unauthorized(
            "This session was used from somewhere else and has been closed. Please sign in again.",
            code="REFRESH_TOKEN_REUSED",
        )
    if result.outcome is not _Outcome.ROTATED or result.user is None or result.token is None:
        raise Unauthorized(INVALID_REFRESH, code="INVALID_REFRESH_TOKEN")
    return result.user, result.token


async def revoke_family(db: Db, family_id: ObjectId) -> None:
    async def attempt(session: AsyncClientSession) -> None:
        await db.refresh_tokens.update_many(
            {"family_id": family_id, "revoked_at": None},
            {"$set": {"revoked_at": utcnow()}},
            session=session,
        )

    await run_in_transaction(db, attempt)


async def end_session(db: Db, presented: str) -> None:
    """Sign out: revoke the family of the presented token. Other devices stay signed in.

    An unknown token is ignored, so logout always succeeds.
    """
    doc = await db.refresh_tokens.find_one(
        {"token_hash": hash_refresh_token(presented)}, {"family_id": 1}
    )
    if doc is not None:
        await revoke_family(db, doc["family_id"])
