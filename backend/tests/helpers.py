from typing import Any

from httpx import AsyncClient
from pymongo.asynchronous.database import AsyncDatabase

from app.models.users import Role, UserCreate
from app.services.users import create_user

DEFAULT_PASSWORD = "long-enough-password"


async def make_user(
    db: AsyncDatabase[dict[str, Any]],
    email: str = "ana@example.com",
    role: Role = Role.ATTENDEE,
    password: str = DEFAULT_PASSWORD,
    display_name: str = "Ana",
) -> dict[str, Any]:
    """Insert a user directly through the service, with any role."""
    data = UserCreate(email=email, password=password, display_name=display_name)
    return await create_user(db.users, data, role=role)


async def login(client: AsyncClient, email: str, password: str = DEFAULT_PASSWORD) -> str:
    response = await client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
