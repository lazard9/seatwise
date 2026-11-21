from fastapi import APIRouter, Response, status
from pymongo.errors import PyMongoError

from app.database.dependencies import Database
from app.models.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(db: Database, response: Response) -> HealthResponse:
    try:
        await db.command("ping")
    except PyMongoError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="unavailable", database="unavailable")
    return HealthResponse(status="ok", database="ok")
