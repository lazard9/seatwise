from typing import Any

from pymongo import AsyncMongoClient


def create_client(url: str, timeout_ms: int) -> AsyncMongoClient[dict[str, Any]]:
    """Create a client. It connects lazily, on the first operation."""
    return AsyncMongoClient(
        url,
        tz_aware=True,
        serverSelectionTimeoutMS=timeout_ms,
    )
