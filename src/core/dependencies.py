from typing import Optional

from fastapi import Depends, Cookie, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import decode_token
from src.db.database import get_db
from src.db.repositories import UserRepository
from src.models.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_current_user(
        token: Optional[str] = Depends(oauth2_scheme),
        access_token: Optional[str] = Cookie(default=None),
        db: AsyncSession = Depends(get_db),
) -> User:
    raw = token or access_token
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не авторизован",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not raw:
        raise credentials_exception

    payload = decode_token(raw)
    if not payload:
        raise credentials_exception

    username: str = payload.get("sub")
    if not username:
        raise credentials_exception

    repo = UserRepository(db)
    user = await repo.get_by_username(username)
    if not user or not user.is_active:
        raise credentials_exception
    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    access_token: Optional[str] = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    try:
        return await get_current_user(token=token, access_token=access_token, db=db)
    except HTTPException:
        return None