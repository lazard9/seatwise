from typing import Annotated

from fastapi import APIRouter, Query

from app.auth.dependencies import AdminUser
from app.database.dependencies import Database
from app.models.common import DEFAULT_PAGE_SIZE, Page, PageNumber, PageSize
from app.models.users import Role, RoleUpdate, UserPublic
from app.services import users as users_service
from app.services.users import serialize_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
async def list_users(
    _admin: AdminUser,
    db: Database,
    page: Annotated[PageNumber, Query()] = 1,
    page_size: Annotated[PageSize, Query()] = DEFAULT_PAGE_SIZE,
    role: Annotated[Role | None, Query()] = None,
    search: Annotated[str | None, Query(max_length=100)] = None,
) -> Page[UserPublic]:
    """All users, newest first. Admin only."""
    docs, total = await users_service.list_users(db.users, page, page_size, role, search)
    return Page(
        items=[serialize_user(doc) for doc in docs], total=total, page=page, page_size=page_size
    )


@router.patch("/{user_id}/role")
async def change_role(user_id: str, data: RoleUpdate, admin: AdminUser, db: Database) -> UserPublic:
    """Set another user's role. Admin only; an admin cannot change their own role."""
    user = await users_service.change_role(db.users, user_id, data.role, admin)
    return serialize_user(user)
