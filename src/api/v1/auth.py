from datetime import timedelta

from fastapi import APIRouter, Request, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.dependencies import get_current_user
from src.core.security import verify_password, create_access_token
from src.db.database import get_db
from src.db.repositories import UserRepository, LogRepository
from src.models.models import User
from src.schemas.schemas import Token, UserRead

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(
        request: Request,
        response: Response,
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    user = await repo.get_by_username(form_data.username)

    log_repo = LogRepository(db)
    ip = request.client.host if request.client else None

    if not user or not verify_password(form_data.password, user.hashed_password):
        await log_repo.create(
            action="LOGIN_FAILED",
            entity="user",
            detail=f"Неверный логин: {form_data.username}",
            ip_address=ip,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт заблокирован",
        )

    token = create_access_token(
        data={"sub": user.username, "role": user.role.value},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    await log_repo.create(
        action="LOGIN",
        entity="user",
        user_id=user.id,
        entity_id=user.id,
        detail=f"Вход: {user.username}",
        ip_address=ip,
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )

    return Token(access_token=token, role=user.role, username=user.username)


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logout successfully"}


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)):
    return current_user