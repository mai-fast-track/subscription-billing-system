from pydantic import BaseModel

from app.core.config import settings


class YookassaPaymentRequest(BaseModel):
    amount_value: str
    currency: str = "RUB"
    return_url: str = settings.YOOKASSA_CALLBACK_RETURN_URL
    type: str = "redirect"
    capture: bool = True
    description: str = "Оформлена подписка"
    payment_method_id: str | None = None  # ID сохраненного платежного метода для автоплатежей
