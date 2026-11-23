from typing import Any

from pymongo import ASCENDING, DESCENDING, IndexModel
from pymongo.asynchronous.database import AsyncDatabase

# Collection name -> indexes. Each later phase adds its collections here (brief, section 5).
INDEXES: dict[str, list[IndexModel]] = {
    "users": [
        IndexModel([("email", ASCENDING)], unique=True, name="email_unique"),
        # The admin user list, newest first.
        IndexModel([("created_at", DESCENDING), ("_id", DESCENDING)], name="created_at_id"),
    ],
    "refresh_tokens": [
        IndexModel([("token_hash", ASCENDING)], unique=True, name="token_hash_unique"),
        IndexModel([("family_id", ASCENDING)], name="family_id"),
        # MongoDB deletes each row once its expires_at has passed.
        IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0, name="expires_at_ttl"),
    ],
}


async def ensure_indexes(db: AsyncDatabase[dict[str, Any]]) -> None:
    """Create every index. Safe to run on each startup: existing indexes are left as they are."""
    for collection, indexes in INDEXES.items():
        await db[collection].create_indexes(indexes)
