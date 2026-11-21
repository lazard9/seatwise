from collections.abc import Awaitable, Callable
from typing import Any

from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.database import AsyncDatabase

type Transaction[T] = Callable[[AsyncClientSession], Awaitable[T]]


async def run_in_transaction[T](db: AsyncDatabase[dict[str, Any]], callback: Transaction[T]) -> T:
    """Run `callback` in a transaction and return its result.

    The driver retries the whole callback on transient errors such as a write
    conflict with a concurrent transaction, so the callback must be safe to run
    again: read what it needs inside the transaction, pass `session` to every
    call, and return a result instead of raising for an expected outcome (an
    exception aborts the transaction, so its writes are lost).
    """
    async with db.client.start_session() as session:
        return await session.with_transaction(callback)
