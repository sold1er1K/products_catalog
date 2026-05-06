from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import require_simple, require_advanced, get_current_user
from src.db.database import get_db
from src.db.repositories import LogRepository, CategoryRepository
from src.models.models import User
from src.schemas.schemas import CategoryRead, CategoryWithProducts, CategoryCreate, CategoryUpdate

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("/", response_model=list[CategoryRead], dependencies=[Depends(require_simple)])
async def list_categories(db: AsyncSession = Depends(get_db)):
    repo = CategoryRepository(db)
    return await repo.get_all()


@router.get("/{category_id}", response_model=CategoryWithProducts, dependencies=[Depends(require_simple)])
async def get_category(category_id: int, db: AsyncSession = Depends(get_db)):
    repo = CategoryRepository(db)
    cats = await repo.get_all_with_products()
    cat = next((c for c in cats if c.id == category_id), None)
    if not cat:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    return cat


@router.post("/", response_model=CategoryRead, dependencies=[Depends(require_advanced)])
async def create_category(
        request: Request,
        payload: CategoryCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    repo = CategoryRepository(db)
    if await repo.get_by_name(payload.name):
        raise HTTPException(status_code=400, detail="Категория с таким именем уже существует")

    cat = await repo.create(name=payload.name, description=payload.description)

    log_repo = LogRepository(db)
    await log_repo.create(
        action="CREATE",
        entity="category",
        user_id=current_user.id,
        entity_id=cat.id,
        detail=f"Создана категория: {cat.name}",
        ip_address=request.client.host if request.client else None,
    )
    return cat


@router.patch("/{category_id}", response_model=CategoryRead, dependencies=[Depends(require_advanced)])
async def update_category(
        category_id: int,
        request: Request,
        payload: CategoryUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    repo = CategoryRepository(db)
    data = payload.model_dump(exclude_none=True)
    cat = await repo.update(category_id, **data)
    if not cat:
        raise HTTPException(status_code=404, detail="Категория не найдена")

    log_repo = LogRepository(db)
    await log_repo.create(
        action="UPDATE",
        entity="category",
        user_id=current_user.id,
        entity_id=category_id,
        detail=f"Обновлена категория id={category_id}: {data}",
        ip_address=request.client.host if request.client else None,
    )
    return cat


@router.delete("/{category_id}", dependencies=[Depends(require_advanced)])
async def delete_category(
        category_id: int,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    repo = CategoryRepository(db)
    ok = await repo.delete(category_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Категория не найдена")

    log_repo = LogRepository(db)
    await log_repo.create(
        action="DELETE",
        entity="category",
        user_id=current_user.id,
        entity_id=category_id,
        detail=f"Удалена категория id={category_id} (каскадно удалены товары)",
        ip_address=request.client.host if request.client else None,
    )
    return {"message": "Категория и все её товары удалены"}