from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)


class PaginatedResponse(BaseModel):
    items: list
    page_index: int
    page_size: int
    total_items: int
    total_pages: int
    has_next_page: bool
    has_previous_page: bool


def paginate(items: list, total: int, page: int, page_size: int) -> PaginatedResponse:
    total_pages = max(1, (total + page_size - 1) // page_size)
    return PaginatedResponse(
        items=items,
        page_index=page,
        page_size=page_size,
        total_items=total,
        total_pages=total_pages,
        has_next_page=page < total_pages,
        has_previous_page=page > 1,
    )


class PartialUpdateMixin(BaseModel):
    fields_to_update: list[str] | None = None


def apply_partial_update(obj, data: dict, fields_to_update: list[str] | None) -> None:
    if fields_to_update is not None:
        allowed = set(fields_to_update)
        data = {k: v for k, v in data.items() if k in allowed}
    for key, value in data.items():
        if hasattr(obj, key):
            setattr(obj, key, value)
    if hasattr(obj, "row_version"):
        obj.row_version = (obj.row_version or 0) + 1
