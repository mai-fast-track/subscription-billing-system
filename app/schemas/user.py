"""
User schemas
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    """Базовая схема пользователя"""

    telegram_id: int = Field(..., gt=0, description="Telegram ID пользователя")


class UserCreate(UserBase):
    """Схема для создания пользователя"""

    pass


class UserUpdate(BaseModel):
    """Схема для обновления пользователя"""

    username: Optional[str] = Field(None, max_length=255, description="Имя пользователя")
    first_name: Optional[str] = Field(None, max_length=255, description="Имя")
    last_name: Optional[str] = Field(None, max_length=255, description="Фамилия")
    is_active: Optional[bool] = Field(None, description="Активен ли пользователь")


class User(UserBase):
    """Схема пользователя для ответа"""

    id: int = Field(..., gt=0, description="ID пользователя")
    telegram_id: int = Field(..., gt=0, description="Telegram ID пользователя")
    role: str = Field(..., description="Роль пользователя")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")

    model_config = ConfigDict(from_attributes=True)
