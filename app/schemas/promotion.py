"""
Promotion schemas
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import PromotionType


class PromotionBase(BaseModel):
    """Базовая схема промокода"""

    code: str = Field(..., min_length=1, max_length=50, description="Код промокода")
    name: str = Field(..., min_length=1, max_length=255, description="Название промокода")
    description: Optional[str] = Field(None, max_length=1000, description="Описание")
    type: PromotionType = Field(..., description="Тип промокода (только bonus_days)")
    value: int = Field(..., ge=0, description="Количество бонусных дней")
    valid_from: datetime = Field(..., description="Дата начала действия")
    valid_until: Optional[datetime] = Field(None, description="Дата окончания действия")
    max_uses: Optional[int] = Field(None, gt=0, description="Максимальное количество использований")
    applicable_plans: Optional[list[str]] = Field(None, description="Список применимых планов")
    assigned_user_id: Optional[int] = Field(
        None, gt=0, description="ID пользователя, которому назначен промокод (None = общий промокод)"
    )

    @field_validator("valid_until")
    @classmethod
    def validate_valid_until(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Валидация: valid_until должна быть позже valid_from"""
        if v and info.data.get("valid_from") and v <= info.data["valid_from"]:
            raise ValueError("valid_until должна быть позже valid_from")
        return v


class PromotionCreate(PromotionBase):
    """Схема для создания промокода"""

    pass


class PromotionUpdate(BaseModel):
    """Схема для обновления промокода"""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Название")
    description: Optional[str] = Field(None, max_length=1000, description="Описание")
    valid_until: Optional[datetime] = Field(None, description="Дата окончания действия")
    is_active: Optional[bool] = Field(None, description="Активен ли промокод")
    max_uses: Optional[int] = Field(None, gt=0, description="Максимальное количество использований")


class PromotionApply(BaseModel):
    """Схема для применения промокода"""

    code: str = Field(..., min_length=1, max_length=50, description="Код промокода")


class ApplyPromotionRequest(BaseModel):
    """Схема запроса для применения промокода к активной подписке"""

    promotion_code: str = Field(..., min_length=1, max_length=50, description="Код промокода")


class ApplyPromotionResponse(BaseModel):
    """Схема ответа при применении промокода к подписке"""

    success: bool = Field(..., description="Успешно ли применен промокод")
    message: str = Field(..., description="Сообщение о результате")
    subscription_id: int = Field(..., gt=0, description="ID подписки")
    old_end_date: datetime = Field(..., description="Дата окончания до применения промокода")
    new_end_date: datetime = Field(..., description="Дата окончания после применения промокода")
    bonus_days: int = Field(..., ge=0, description="Количество добавленных бонусных дней")

    model_config = ConfigDict(from_attributes=True)


class Promotion(PromotionBase):
    """Схема промокода для ответа"""

    id: int = Field(..., gt=0, description="ID промокода")
    is_active: bool = Field(..., description="Активен ли промокод")
    current_uses: int = Field(..., ge=0, description="Текущее количество использований")
    assigned_user_id: Optional[int] = Field(None, gt=0, description="ID пользователя, которому назначен промокод")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")

    model_config = ConfigDict(from_attributes=True)
