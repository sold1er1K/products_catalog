from sqlalchemy import select

from src.core.security import get_password_hash
from src.db.database import AsyncSessionLocal, create_tables
from src.models.models import User, UserRole, Category, Product


async def seed():
    await create_tables()

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == "admin"))
        if result.scalar_one_or_none():
            return

        # users
        users = [
            User(username="admin", email="admin@example.com",
                 hashed_password=get_password_hash("admin123"), role=UserRole.admin),
            User(username="advanced", email="advanced@example.com",
                 hashed_password=get_password_hash("advanced123"), role=UserRole.advanced),
            User(username="user", email="user@example.com",
                 hashed_password=get_password_hash("user123"), role=UserRole.simple),
        ]
        session.add_all(users)
        await session.flush()

        # categories
        cat_food = Category(name="Еда", description="Продукты питания")
        cat_sweets = Category(name="Вкусности", description="Сладости и лакомства")
        cat_drinks = Category(name="Вода", description="Напитки и вода")
        session.add_all([cat_food, cat_sweets, cat_drinks])
        await session.flush()

        # products
        products = [
            Product(
                name="Селедка",
                category_id=cat_food.id,
                description="Селедка соленая",
                price=10.000,
                note_general="Акция",
                note_special="Пересоленая",
            ),
            Product(
                name="Тушенка",
                category_id=cat_food.id,
                description="Тушенка говяжья",
                price=20.000,
                note_general="Вкусная",
                note_special="Жилы",
            ),
            Product(
                name="Сгущенка",
                category_id=cat_sweets.id,
                description="В банках",
                price=30.000,
                note_general="С ключом",
                note_special="Вкусная",
            ),
            Product(
                name="Квас",
                category_id=cat_drinks.id,
                description="В бутылках",
                price=15.000,
                note_general="Вятский",
                note_special="Теплый",
            ),
        ]
        session.add_all(products)
        await session.commit()