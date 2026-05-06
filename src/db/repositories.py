from typing import Optional, Sequence, Generic, Type, TypeVar

from sqlalchemy import select, update, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.database import Base
from src.models.models import User, UserRole, Log

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    def __init__(self, model: Type[ModelT], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, entity_id: int) -> Optional[ModelT]:
        result = await self.session.execute(
            select(self.model).where(self.model.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[ModelT]:
        result = await self.session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def delete(self, entity_id: int) -> bool:
        result = await self.session.execute(
            delete(self.model).where(self.model.id == entity_id)
        )
        return result.rowcount > 0


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()


class LogRepository(BaseRepository[Log]):
    def __init__(self, session: AsyncSession):
        super().__init__(Log, session)

    async def create(
        self,
        action: str,
        entity: str,
        user_id: Optional[int] = None,
        entity_id: Optional[int] = None,
        detail: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Log:
        log = Log(
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            detail=detail,
            ip_address=ip_address,
        )
        self.session.add(log)
        await self.session.flush()
        return log