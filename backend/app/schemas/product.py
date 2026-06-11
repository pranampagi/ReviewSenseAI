"""Product API schemas — create, update, read, and paginated list responses."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    """Body for ``POST /products``."""

    name: str = Field(min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    description: str | None = None


class ProductUpdate(BaseModel):
    """Body for ``PUT /products/{id}`` — only provided fields are updated."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    description: str | None = None


class ProductRead(BaseModel):
    """Single product returned from list or detail endpoints."""

    id: uuid.UUID
    name: str
    category: str | None
    description: str | None
    created_at: datetime
    owner_id: uuid.UUID

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    """Paginated product list for the authenticated owner."""

    items: list[ProductRead]
    total: int
    page: int
    pages: int
