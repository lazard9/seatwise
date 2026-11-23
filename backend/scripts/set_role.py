"""Set the role of an existing account, e.g. to make the first admin.

    uv run python -m scripts.set_role --email you@example.com --role admin

Sign up through the app first; registration always creates an attendee.
"""

import argparse
import asyncio
import sys
from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.models.users import Role
from app.services.users import find_user_by_email
from scripts._db import open_database


async def set_role(db: AsyncDatabase[dict[str, Any]], email: str, role: Role) -> bool:
    """Return False when no account has this email."""
    user = await find_user_by_email(db.users, email)
    if user is None:
        return False
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"role": role.value}})
    return True


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--email", required=True)
    parser.add_argument("--role", required=True, choices=[role.value for role in Role])
    args = parser.parse_args()

    async with open_database() as db:
        if not await set_role(db, args.email, Role(args.role)):
            sys.exit(f"No account with email {args.email}")
    print(f"{args.email} is now {args.role}")


if __name__ == "__main__":
    asyncio.run(main())
