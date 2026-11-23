from typing import Annotated

from pydantic import BaseModel, Field

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

PageNumber = Annotated[int, Field(ge=1)]
PageSize = Annotated[int, Field(ge=1, le=MAX_PAGE_SIZE)]


class Page[T](BaseModel):
    """One page of a list. Every paginated endpoint returns this shape."""

    items: list[T]
    total: int
    page: int
    page_size: int
