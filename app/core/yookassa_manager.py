from yookassa import Configuration

from app.core.config import settings


class YookassaManager:
    """Оборачиваем Yookassa, чтобы избежать проблем с глобальным состоянием"""

    def __init__(self):
        self.configured = False

    def configure(self):
        """Конфигурируем один раз"""
        if not self.configured:
            Configuration.configure(
                account_id=str(settings.YOOKASSA_SHOP_ID),
                secret_key=settings.YOOKASSA_SECRET_KEY,
            )
            self.configured = True


yookassa_manager = YookassaManager()
