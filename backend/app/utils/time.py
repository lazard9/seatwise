from datetime import UTC, datetime


def utcnow() -> datetime:
    """Current time, timezone-aware UTC. Use this instead of `datetime.now()`."""
    return datetime.now(UTC)
