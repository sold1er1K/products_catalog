from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_user, require_admin
from src.core.security import get_password_hash
from src.db.database import get_db
from src.db.repositories import UserRepository, LogRepository
from src.models.models import User
from src.schemas.schemas import UserRead, UserCreate, UserUpdate, UserPasswordChange

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/", response_model=list[UserRead], dependencies=[Depends(require_admin)])
async def list_users(db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    return await repo.get_all()


@router.post("/", response_model=UserRead, dependencies=[Depends(require_admin)])
async def create_user(
        request: Request,
        payload: UserCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    repo = UserRepository(db)
    if await repo.get_by_username(payload.username):
        raise HTTPException(status_code=400, detail="Имя пользователя занято")
    if await repo.get_by_email(payload.email):
        raise HTTPException(status_code=400, detail="Email уже используется")

    user = await repo.create(
        username=payload.username,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
    )

    log_repo = LogRepository(db)
    await log_repo.create(
        action="CREATE",
        entity="user",
        user_id=current_user.id,
        entity_id=user.id,
        detail=f"Создан пользователь: {user.username}",
        ip_address=request.client.host if request.client else None,
    )
    return user


@router.patch("/{user_id}", response_model=UserRead, dependencies=[Depends(require_admin)])
async def update_user(
        user_id: int,
        request: Request,
        payload: UserUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    repo = UserRepository(db)
    data = payload.model_dump(exclude_none=True)
    user = await repo.update(user_id, **data)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    log_repo = LogRepository(db)
    await log_repo.create(
        action="UPDATE",
        entity="user",
        user_id=current_user.id,
        entity_id=user_id,
        detail=f"Обновлён пользователь id={user_id}: {data}",
        ip_address=request.client.host if request.client else None,
    )
    return user


@router.post("/{user_id}/change-password", dependencies=[Depends(require_admin)])
async def change_password(
        user_id: int,
        request: Request,
        payload: UserPasswordChange,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    repo = UserRepository(db)
    ok = await repo.update_password(user_id, get_password_hash(payload.new_password))
    if not ok:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    log_repo = LogRepository(db)
    await log_repo.create(
        action="CHANGE_PASSWORD",
        entity="user",
        user_id=current_user.id,
        entity_id=user_id,
        detail=f"Смена пароля для id={user_id}",
        ip_address=request.client.host if request.client else None,
    )
    return {"message": "Пароль изменён"}


@router.delete("/{user_id}", dependencies=[Depends(require_admin)])
async def delete_user(
        user_id: int,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Нельзя удалить самого себя")
    repo = UserRepository(db)
    ok = await repo.delete(user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    log_repo = LogRepository(db)
    await log_repo.create(
        action="DELETE",
        entity="user",
        user_id=current_user.id,
        entity_id=user_id,
        detail=f"Удалён пользователь id={user_id}",
        ip_address=request.client.host if request.client else None,
    )
    return {"message": "Пользователь удалён"}