from typing import Any

import pytest
from pymongo.asynchronous.database import AsyncDatabase


@pytest.fixture(autouse=True)
async def clean_collections(db: AsyncDatabase[dict[str, Any]]) -> None:
    """Empty every collection before each test. Indexes stay, so tests see the real constraints."""
    for name in await db.list_collection_names():
        await db[name].delete_many({})
