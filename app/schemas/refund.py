"""
Refund schemas
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RefundSchema(BaseModel):
    """Базовая схема возврата"""

    payment_id: int = Field(..., gt=0, description="ID платежа")
    yookassa_refund_id: str = Field(..., description="ID возврата в Юкассе")
    amount: float = Field(..., ge=0, description="Сумма возврата")
    currency: str = Field(default="RUB", description="Валюта")
    status: str = Field(..., description="Статус возврата")
    reason: str | None = Field(None, description="Причина возврата")

    model_config = ConfigDict(from_attributes=True)


class RefundResponse(BaseModel):
    """Полная информация о возврате"""

    id: int = Field(..., gt=0, description="ID возврата")
    payment_id: int = Field(..., gt=0, description="ID платежа")
    yookassa_refund_id: str = Field(..., description="ID возврата в Юкассе")
    amount: float = Field(..., ge=0, description="Сумма возврата")
    currency: str = Field(default="RUB", description="Валюта")
    status: str = Field(..., description="Статус возврата")
    reason: str | None = Field(None, description="Причина возврата")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")

    model_config = ConfigDict(from_attributes=True)


class RefundCreateRequest(BaseModel):
    """Запрос на создание возврата"""

    payment_id: int = Field(..., gt=0, description="ID платежа")
    amount: float | None = Field(None, ge=0, description="Сумма возврата (если None - полный возврат)")
    reason: str | None = Field(None, max_length=500, description="Причина возврата")
