from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import require_admin
from src.db.database import get_db
from src.db.repositories import LogRepository

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("/", dependencies=[Depends(require_admin)])
async def get_logs(limit: int = 100, db: AsyncSession = Depends(get_db)):
    repo = LogRepository(db)
    logs = await repo.get_recent(limit=limit)
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "username": log.user.username if log.user else "—",
            "action": log.action,
            "entity": log.entity,
            "entity_id": log.entity_id,
            "detail": log.detail,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]