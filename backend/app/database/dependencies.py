from typing import Annotated, Any

from fastapi import Depends, Request
from pymongo.asynchronous.database import AsyncDatabase


def get_database(request: Request) -> AsyncDatabase[dict[str, Any]]:
    return request.app.state.db


Database = Annotated[AsyncDatabase[dict[str, Any]], Depends(get_database)]
