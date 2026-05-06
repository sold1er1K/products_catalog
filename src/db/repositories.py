from typing import Optional, Sequence, Generic, Type, TypeVar

from sqlalchemy import select, update, func, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.database import Base
from src.models.models import User, UserRole, Log, Category, Product

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

    async def create(self, username: str, email: str, hashed_password: str, role: UserRole) -> User:
        user = User(username=username, email=email, hashed_password=hashed_password, role=role)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update_password(self, user_id: int, hashed_password: str) -> bool:
        result = await self.session.execute(
            update(User).where(User.id == user_id).values(hashed_password=hashed_password)
        )
        return result.rowcount > 0

    async def update(self, user_id: int, **kwargs) -> Optional[User]:
        await self.session.execute(
            update(User).where(User.id == user_id).values(**kwargs)
        )
        return await self.get_by_id(user_id)


class CategoryRepository(BaseRepository[Category]):
    def __init__(self, session: AsyncSession):
        super().__init__(Category, session)

    async def get_all_with_products(self) -> Sequence[Category]:
        result = await self.session.execute(
            select(Category).options(selectinload(Category.products))
        )
        return result.scalars().all()

    async def get_by_name(self, name: str) -> Optional[Category]:
        result = await self.session.execute(
            select(Category).where(Category.name == name)
        )
        return result.scalar_one_or_none()

    async def create(self, name: str, description: Optional[str] = None) -> Category:
        cat = Category(name=name, description=description)
        self.session.add(cat)
        await self.session.flush()
        await self.session.refresh(cat)
        return cat

    async def update(self, category_id: int, **kwargs) -> Optional[Category]:
        await self.session.execute(
            update(Category).where(Category.id == category_id).values(**kwargs)
        )
        return await self.get_by_id(category_id)


class ProductRepository(BaseRepository[Product]):
    def __init__(self, session: AsyncSession):
        super().__init__(Product, session)

    async def get_all_with_category(
            self,
            skip: int = 0,
            limit: int = 100,
            search: Optional[str] = None,
            category_id: Optional[int] = None,
    ) -> Sequence[Product]:
        q = select(Product).options(selectinload(Product.category))
        if search:
            q = q.where(
                or_(
                    Product.name.ilike(f"%{search}%"),
                    Product.description.ilike(f"%{search}%"),
                )
            )
        if category_id:
            q = q.where(Product.category_id == category_id)
        q = q.offset(skip).limit(limit).order_by(Product.id)
        result = await self.session.execute(q)
        return result.scalars().all()

    async def get_with_category(self, product_id: int) -> Optional[Product]:
        result = await self.session.execute(
            select(Product)
            .options(selectinload(Product.category))
            .where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> Product:
        product = Product(**kwargs)
        self.session.add(product)
        await self.session.flush()
        return await self.get_with_category(product.id)

    async def update(self, product_id: int, **kwargs) -> Optional[Product]:
        await self.session.execute(
            update(Product).where(Product.id == product_id).values(**kwargs)
        )
        return await self.get_with_category(product_id)

    async def count(
            self,
            search: Optional[str] = None,
            category_id: Optional[int] = None,
    ) -> int:
        q = select(func.count(Product.id))
        if search:
            q = q.where(
                or_(
                    Product.name.ilike(f"%{search}%"),
                    Product.description.ilike(f"%{search}%"),
                )
            )
        if category_id:
            q = q.where(Product.category_id == category_id)
        result = await self.session.execute(q)
        return result.scalar_one()


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