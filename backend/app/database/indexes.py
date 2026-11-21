from typing import Any

from pymongo import ASCENDING, IndexModel
from pymongo.asynchronous.database import AsyncDatabase

# Collection name -> indexes. Each later phase adds its collections here (brief, section 5).
INDEXES: dict[str, list[IndexModel]] = {
    "users": [
        IndexModel([("email", ASCENDING)], unique=True, name="email_unique"),
    ],
}


async def ensure_indexes(db: AsyncDatabase[dict[str, Any]]) -> None:
    """Create every index. Safe to run on each startup: existing indexes are left as they are."""
    for collection, indexes in INDEXES.items():
        await db[collection].create_indexes(indexes)
