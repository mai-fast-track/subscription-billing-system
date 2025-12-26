from datetime import datetime, timedelta
from typing import Any, Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer

from app.core.config import settings
from app.core.enums import UserRole
from app.schemas.auth import TokenData

security = HTTPBearer()


class JWTHandler:
    """Handles JWT token creation and verification"""

    @staticmethod
    def create_access_token(
        user_id: int, telegram_id: int, role: str, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        payload = {"user_id": user_id, "telegram_id": telegram_id, "role": role}

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + settings.access_token_expire_timedelta

        payload.update({"exp": expire, "iat": datetime.utcnow()})

        try:
            encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
            return encoded_jwt
        except Exception as e:
            raise ValueError(f"Error encoding JWT: {str(e)}")

    @staticmethod
    def verify_token(token: str) -> dict[str, Any]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise jwt.ExpiredSignatureError("Token has expired")
        except jwt.InvalidSignatureError:
            raise jwt.InvalidSignatureError("Invalid token signature")
        except jwt.InvalidTokenError as e:
            raise jwt.InvalidTokenError(f"Invalid token: {str(e)}")


async def verify_bot_request(request: Request):
    """
    Проверяет, что запрос от авторизованного бота
    """
    bot_token = request.headers.get("X-Bot-Token")

    if not bot_token or bot_token != settings.BOT_SECRET_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bot token")

    return None


async def get_current_user(credentials=Depends(security)) -> TokenData:
    """
    Dependency to verify JWT token and get current user
    """
    token = credentials.credentials

    try:
        payload = JWTHandler.verify_token(token)

        user_id: int = payload.get("user_id")
        telegram_id: int = payload.get("telegram_id")
        role_str: str = payload.get("role")

        if user_id is None or telegram_id is None or role_str is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        try:
            role = UserRole(role_str)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid role in token")

        token_data = TokenData(user_id=user_id, telegram_id=telegram_id, role=role)

        return token_data

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token signature")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def get_current_admin(token_data: TokenData = Depends(get_current_user)) -> TokenData:
    """
    Dependency to verify that current user is admin
    """
    if token_data.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can access this resource")
    return token_data
