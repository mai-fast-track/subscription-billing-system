"""
Subscription schemas
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import SubscriptionStatus


# SubscriptionPlan схемы
class SubscriptionPlanSchema(BaseModel):
    """Базовая схема плана подписки"""

    name: str = Field(..., min_length=1, max_length=255, description="Название плана")
    price: float = Field(..., ge=0, description="Цена плана")
    duration_days: int = Field(..., gt=0, description="Длительность в днях")
    features: Optional[str] = Field(None, max_length=2000, description="Описание возможностей")


class SubscriptionPlanCreateRequest(SubscriptionPlanSchema):
    """Схема для создания плана подписки"""

    pass


class SubscriptionPlanUpdate(BaseModel):
    """Схема для обновления плана подписки"""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Название плана")
    price: Optional[float] = Field(None, ge=0, description="Цена плана")
    duration_days: Optional[int] = Field(None, gt=0, description="Длительность в днях")
    features: Optional[str] = Field(None, max_length=2000, description="Описание возможностей")


class SubscriptionPlanResponse(SubscriptionPlanSchema):
    """Схема плана подписки для ответа"""

    id: int = Field(..., gt=0, description="ID плана")
    created_at: datetime = Field(..., description="Дата создания")

    model_config = ConfigDict(from_attributes=True)


class SubscriptionSchema(BaseModel):
    """Схема подписки"""

    plan_id: int = Field(..., gt=0, description="ID плана подписки")
    status: SubscriptionStatus = Field(default=SubscriptionStatus.active, description="Статус подписки")
    start_date: datetime = Field(..., description="Дата начала подписки")
    end_date: datetime = Field(..., description="Дата окончания подписки")

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: datetime, info) -> datetime:
        """Валидация: end_date должна быть позже start_date"""
        if info.data.get("start_date") and v <= info.data["start_date"]:
            raise ValueError("end_date должна быть позже start_date")
        return v

    model_config = ConfigDict(from_attributes=True)


class SubscriptionCreateRequestSchema(BaseModel):
    """Схема для создания подписки"""

    user_id: int = Field(..., gt=0, description="ID пользователя")
    plan_id: int = Field(..., gt=0, description="ID плана подписки")
    start_date: Optional[datetime] = Field(None, description="Дата начала подписки")
    status: Optional[SubscriptionStatus] = Field(None, description="Статус подписки")


class SubscriptionUpdate(BaseModel):
    """Схема для обновления подписки"""

    status: Optional[SubscriptionStatus] = Field(None, description="Статус подписки")
    end_date: Optional[datetime] = Field(None, description="Дата окончания подписки")


class SubscriptionResponse(SubscriptionSchema):
    """Схема подписки для ответа"""

    id: int = Field(..., gt=0, description="ID подписки")
    user_id: int = Field(..., gt=0, description="ID пользователя")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")

    model_config = ConfigDict(from_attributes=True)


class SubscriptionDetailResponse(SubscriptionResponse):
    """Расширенный ответ с информацией о плане"""

    plan: SubscriptionPlanResponse = Field(..., description="Информация о плане подписки")


# Юзер со своей подпиской
class UserSubscriptionInfo(BaseModel):
    """Информация о подписках пользователя"""

    active_subscription: Optional[SubscriptionDetailResponse] = Field(None, description="Активная подписка")
    subscription_history: list[SubscriptionResponse] = Field(default_factory=list, description="История подписок")

    model_config = ConfigDict(from_attributes=True)


# Схемы для SubscriptionOrchestratorService
class SubscriptionWithPaymentRequest(BaseModel):
    """Схема для создания подписки с платежом (обычное оформление без промопериода)"""

    user_id: int = Field(..., gt=0, description="ID пользователя")
    plan_id: int = Field(..., gt=0, description="ID плана подписки")
    return_url: str = Field(..., min_length=10, description="URL для возврата после оплаты")


class SubscriptionWithPaymentResponse(BaseModel):
    """Схема ответа при создании подписки с платежом"""

    subscription_id: int = Field(..., gt=0, description="ID созданной подписки")
    payment_id: int = Field(..., gt=0, description="ID созданного платежа")
    confirmation_url: Optional[str] = Field(None, description="URL для подтверждения оплаты (None для промопериода)")
    yookassa_payment_id: Optional[str] = Field(None, description="ID платежа в Юкассе (None для промопериода)")
    message: str = Field(..., description="Сообщение о результате")
    is_trial: bool = Field(default=False, description="Флаг промопериода")

    model_config = ConfigDict(from_attributes=True)


# Схемы для промопериода
class TrialEligibilityResponse(BaseModel):
    """Схема ответа для проверки доступности промопериода"""

    is_eligible: bool = Field(..., description="Доступен ли промопериод для пользователя")
    reason: Optional[str] = Field(None, description="Причина недоступности (если is_eligible=False)")


class CreateTrialRequest(BaseModel):
    """Схема для создания промопериода"""

    user_id: int = Field(..., gt=0, description="ID пользователя")
    plan_id: int = Field(..., gt=0, description="ID плана подписки")


class CreateTrialResponse(BaseModel):
    """Схема ответа при создании промопериода"""

    subscription_id: int = Field(..., gt=0, description="ID созданной подписки")
    payment_id: int = Field(..., gt=0, description="ID созданного платежа")
    end_date: datetime = Field(..., description="Дата окончания промопериода")
    message: str = Field(..., description="Сообщение о результате")

    model_config = ConfigDict(from_attributes=True)


class CancelSubscriptionRequest(BaseModel):
    """Схема запроса на отмену подписки"""

    with_refund: bool = Field(
        default=False,
        description=(
            "Выполнить возврат средств. "
            "Если True - подписка отменяется сразу с возвратом за неиспользованную часть. "
            "Если False - подписка активна до end_date без возврата (по умолчанию)"
        ),
    )
