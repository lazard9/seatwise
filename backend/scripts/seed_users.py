"""Create one demo account per role for local development.

    uv run python -m scripts.seed_users --password <at least 8 characters>

Running it again is safe: existing accounts keep their password and get their
demo role back.
"""

import argparse
import asyncio
from typing import Any

from pydantic import ValidationError
from pymongo.asynchronous.database import AsyncDatabase

from app.errors import Conflict
from app.models.users import Role, UserCreate
from app.services.users import create_user
from scripts._db import open_database

DEMO_USERS = [
    ("admin@example.com", "Admin", Role.ADMIN),
    ("organizer@example.com", "Organizer", Role.ORGANIZER),
    ("attendee@example.com", "Attendee", Role.ATTENDEE),
]


async def seed_users(db: AsyncDatabase[dict[str, Any]], password: str) -> list[tuple[str, str]]:
    """Return (email, "created" | "exists") per demo account."""
    results = []
    for email, name, role in DEMO_USERS:
        data = UserCreate(email=email, password=password, display_name=name)
        try:
            await create_user(db.users, data, role=role)
            results.append((email, "created"))
        except Conflict:
            await db.users.update_one({"email": email}, {"$set": {"role": role.value}})
            results.append((email, "exists"))
    return results


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--password", required=True, help="password for all demo accounts")
    args = parser.parse_args()

    try:
        UserCreate(email=DEMO_USERS[0][0], password=args.password, display_name="Check")
    except ValidationError as exc:
        parser.error(f"invalid password: {exc.errors()[0]['msg']}")

    async with open_database() as db:
        for email, outcome in await seed_users(db, args.password):
            print(f"{outcome:8} {email}")


if __name__ == "__main__":
    asyncio.run(main())
