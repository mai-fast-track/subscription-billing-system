"""
Authentication endpoints
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_uow
from app.database.unit_of_work import UnitOfWork
from app.schemas.auth import TelegramAuth, Token
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/telegram",
    response_model=Token,
    summary="Authenticate via Telegram",
    description="Bot sends telegram_id and gets JWT",
)
async def auth_telegram(auth_data: TelegramAuth, uow: UnitOfWork = Depends(get_uow)) -> Token:
    """
    Аутентификация через Telegram

    Поток:
    1. Bot send telegram_id
    2. App find/create user
    3. App generate jwt
    4. return token
    """
    async with uow:
        try:
            if not auth_data.telegram_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="telegram_id is required")

            service = AuthService(uow)
            user, token = await service.authenticate_telegram_user(auth_data)

            logger.info(f"Auth success: user_id={user.id}, telegram_id={user.telegram_id}")

            return Token(access_token=token, token_type="bearer")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during authentication"
            )
