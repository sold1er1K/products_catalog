from typing import Optional

from fastapi import APIRouter, Query, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import require_simple, get_current_user, require_advanced
from src.db.database import get_db
from src.db.repositories import LogRepository, ProductRepository
from src.models.models import UserRole, User
from src.schemas.schemas import ProductUpdate, ProductCreate

router = APIRouter(prefix="/api/products", tags=["products"])


def _serialize_product(p, role: UserRole) -> dict:
    data = {
        "id": p.id,
        "name": p.name,
        "category_id": p.category_id,
        "category_name": p.category.name if p.category else None,
        "description": p.description,
        "price": float(p.price),
        "note_general": p.note_general,
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
    }

    if role in (UserRole.advanced, UserRole.admin):
        data["note_special"] = p.note_special
    return data


@router.get("/")
async def list_products(
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=200),
        search: Optional[str] = Query(None),
        category_id: Optional[int] = Query(None),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(require_simple),
):
    repo = ProductRepository(db)
    products = await repo.get_all_with_category(skip=skip, limit=limit, search=search, category_id=category_id)
    total = await repo.count(search=search, category_id=category_id)
    return {
        "total": total,
        "items": [_serialize_product(p, current_user.role) for p in products],
    }


@router.get("/{product_id}")
async def get_product(
        product_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(require_simple),
):
    repo = ProductRepository(db)
    p = await repo.get_with_category(product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return _serialize_product(p, current_user.role)


@router.post("/", dependencies=[Depends(require_simple)])
async def create_product(
        request: Request,
        payload: ProductCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    repo = ProductRepository(db)
    p = await repo.create(**payload.model_dump())

    log_repo = LogRepository(db)
    await log_repo.create(
        action="CREATE",
        entity="product",
        user_id=current_user.id,
        entity_id=p.id,
        detail=f"Создан товар: {p.name}",
        ip_address=request.client.host if request.client else None,
    )
    return _serialize_product(p, current_user.role)


@router.patch("/{product_id}", dependencies=[Depends(require_simple)])
async def update_product(
        product_id: int,
        request: Request,
        payload: ProductUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    repo = ProductRepository(db)
    data = payload.model_dump(exclude_none=True)

    if current_user.role == UserRole.simple and "note_special" in data:
        del data["note_special"]

    p = await repo.update(product_id, **data)
    if not p:
        raise HTTPException(status_code=404, detail="Товар не найден")

    log_repo = LogRepository(db)
    await log_repo.create(
        action="UPDATE",
        entity="product",
        user_id=current_user.id,
        entity_id=product_id,
        detail=f"Обновлён товар id={product_id}: {list(data.keys())}",
        ip_address=request.client.host if request.client else None,
    )
    return _serialize_product(p, current_user.role)


@router.delete("/{product_id}", dependencies=[Depends(require_advanced)])
async def delete_product(
        product_id: int,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    repo = ProductRepository(db)
    ok = await repo.delete(product_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Товар не найден")

    log_repo = LogRepository(db)
    await log_repo.create(
        action="DELETE",
        entity="product",
        user_id=current_user.id,
        entity_id=product_id,
        detail=f"Удалён товар id={product_id}",
        ip_address=request.client.host if request.client else None,
    )
    return {"message": "Товар удалён"}