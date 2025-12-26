"""
Payment schemas
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import PaymentStatus


class PaymentCreateRequest(BaseModel):
    """Запрос на создание платежа"""

    user_id: int = Field(..., gt=0, description="ID пользователя")
    subscription_id: int = Field(..., gt=0, description="ID подписки")
    amount: float = Field(..., gt=0, description="Сумма платежа")
    return_url: str = Field(..., min_length=10, description="URL для возврата после оплаты")


class ChangePaymentMethodRequest(BaseModel):
    """Запрос на смену карты для автосписаний"""

    user_id: int = Field(..., gt=0, description="ID пользователя")
    return_url: str = Field(..., min_length=10, description="URL для возврата после оплаты")
    amount: float = Field(default=1.0, gt=0, description="Минимальная сумма для привязки карты (по умолчанию 1 рубль)")


class PaymentCreateResponse(BaseModel):
    """Ответ: платеж создан, вот ссылка на оплату"""

    success: bool = Field(..., description="Успешно ли создан платеж")
    message: str = Field(..., description="Сообщение")
    confirmation_url: str = Field(..., description="URL для подтверждения оплаты")
    yookassa_payment_id: str = Field(..., description="ID платежа в Юкассе")


class PaymentResponse(BaseModel):
    """Полная информация о платеже"""

    id: int = Field(..., gt=0, description="ID платежа")
    user_id: int = Field(..., gt=0, description="ID пользователя")
    subscription_id: int = Field(..., gt=0, description="ID подписки")
    yookassa_payment_id: str = Field(..., description="ID платежа в Юкассе")
    amount: float = Field(..., ge=0, description="Сумма платежа")
    currency: str = Field(default="RUB", description="Валюта")
    status: PaymentStatus = Field(..., description="Статус платежа")
    payment_method: str | None = Field(None, description="Метод платежа")
    attempt_number: int = Field(default=1, description="Номер попытки")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")

    model_config = ConfigDict(from_attributes=True)


class PaymentWithSubscriptionResponse(PaymentResponse):
    """Платеж с информацией о подписке и возвратах"""

    subscription_plan_name: str | None = Field(None, description="Название плана подписки")
    subscription_status: str | None = Field(None, description="Статус подписки")
    refund_amount: float | None = Field(None, ge=0, description="Сумма возврата (если есть)")
    refund_status: str | None = Field(None, description="Статус возврата (pending, succeeded, failed, cancelled)")
