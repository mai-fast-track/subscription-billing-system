"""
FastAPI dependencies
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clients import yookassa_client
from app.core.database import get_db
from app.core.yookassa_manager import yookassa_manager

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security), db: AsyncSession = Depends(get_db)
):
    """Получить текущего аутентифицированного пользователя из JWT токена"""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Authentication not implemented")


def get_yookassa_manager():
    """Зависимость возвращает глобальный менеджер"""
    if not yookassa_manager.configured:
        raise HTTPException(500, "ЮKassa не сконфигурирована")
    return yookassa_manager


def get_yookassa_client():
    """Зависимость возвращает клиента Юкассы"""
    if not yookassa_manager.configured:
        raise HTTPException(500, "ЮKassa не инициализирована")
    return yookassa_client
