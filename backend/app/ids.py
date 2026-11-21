from bson import ObjectId
from bson.errors import InvalidId

from app.errors import BadRequest


def parse_object_id(value: str, what: str = "id") -> ObjectId:
    """Parse a path or body id. A malformed id is a client bug, so it is 400, not 404."""
    try:
        return ObjectId(value)
    except (InvalidId, TypeError) as exc:
        raise BadRequest(f"Invalid {what}", code="INVALID_ID") from exc
