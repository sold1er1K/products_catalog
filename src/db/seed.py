from src.core.security import get_password_hash
from src.db.database import AsyncSessionLocal, create_tables
from src.models.models import User, UserRole


async def seed():
    await create_tables()

    async with AsyncSessionLocal() as session:
        users = [
            User(username="admin", email="admin@example.com",
                 hashed_password=get_password_hash("admin123"), role=UserRole.admin),
            User(username="advanced", email="advanced@example.com",
                 hashed_password=get_password_hash("advanced123"), role=UserRole.advanced),
            User(username="user", email="user@example.com",
                 hashed_password=get_password_hash("user123"), role=UserRole.simple),
        ]
        session.add_all(users)
        await session.commit()