"""Product CRUD routes — scoped to the authenticated user's catalog."""

import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.product import Product
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductRead,
    ProductUpdate,
)

router = APIRouter(tags=["products"])


async def _get_owned_product(
    product_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> Product:
    """Load a product by id and ensure it belongs to ``current_user``."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if product.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@router.get("", response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProductListResponse:
    """List products owned by the current user with optional name/category search."""
    base = select(Product).where(Product.owner_id == current_user.id)
    count_base = select(func.count()).select_from(Product).where(Product.owner_id == current_user.id)

    if search.strip():
        pattern = f"%{search.strip()}%"
        search_filter = or_(Product.name.ilike(pattern), Product.category.ilike(pattern))
        base = base.where(search_filter)
        count_base = count_base.where(search_filter)

    total_result = await db.execute(count_base)
    total = total_result.scalar_one()

    offset = (page - 1) * limit
    result = await db.execute(
        base.order_by(Product.created_at.desc()).offset(offset).limit(limit)
    )
    items = result.scalars().all()
    pages = max(1, math.ceil(total / limit)) if total else 1

    return ProductListResponse(
        items=[ProductRead.model_validate(p) for p in items],
        total=total,
        page=page,
        pages=pages,
    )


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    body: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Product:
    """Create a new product owned by the current user."""
    product = Product(
        owner_id=current_user.id,
        name=body.name,
        category=body.category,
        description=body.description,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Product:
    """Return one product if it exists and belongs to the current user."""
    return await _get_owned_product(product_id, current_user, db)


@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: uuid.UUID,
    body: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Product:
    """Partially update a product (only fields sent in the body are changed)."""
    product = await _get_owned_product(product_id, current_user, db)
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    for field, value in updates.items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a product owned by the current user."""
    product = await _get_owned_product(product_id, current_user, db)
    await db.delete(product)
    await db.commit()
