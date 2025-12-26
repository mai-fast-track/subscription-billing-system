from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.core.enums import UserRole


class TelegramAuth(BaseModel):
    """Telegram authentication request"""

    telegram_id: int = Field(..., gt=0, description="Telegram user ID")


class TokenData(BaseModel):
    """Token payload data"""

    user_id: int
    telegram_id: int
    role: UserRole


class Token(BaseModel):
    """Token response"""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User response model"""

    id: int
    telegram_id: int
    role: UserRole
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Error(BaseModel):
    """Error response model"""

    detail: str
    error_code: Optional[str] = None
