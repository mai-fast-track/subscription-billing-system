"""
Application configuration
"""

from datetime import timedelta

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Billing Core"
    DEBUG: bool = False
    PORT: int = 8000

    # Database
    DATABASE_URL: str  # Обязательная переменная

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    BOT_SECRET_TOKEN: str

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    BOT_TOKEN: str
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # Notifications
    NOTIFICATION_RETRY_ATTEMPTS: int = 3
    NOTIFICATION_RETRY_DELAY: int = 60

    # Payment retry
    PAYMENT_RETRY_ATTEMPTS: int = 3
    PAYMENT_RETRY_DELAY: int = 300

    # Subscription renewal
    RENEWAL_CHECK_INTERVAL: int = 3600

    # Auto Payment Configuration
    AUTO_PAYMENT_START_HOUR: int = 2  # Начало дня для обработки автосписаний (02:00)
    AUTO_PAYMENT_START_MINUTE: int = 0
    AUTO_PAYMENT_END_HOUR: int = 23  # Конец дня для обработки cancelled_waiting (23:00)
    AUTO_PAYMENT_END_MINUTE: int = 0
    AUTO_PAYMENT_MAX_ATTEMPTS: int = 3  # Максимум попыток автосписания
    AUTO_PAYMENT_RETRY_INTERVAL_SECONDS: int = 60  # Интервал между попытками (в секундах)
    AUTO_PAYMENT_REDIS_TTL_HOURS: int = 24  # TTL для ключей Redis (часы)

    # Trial Period Configuration
    TRIAL_PERIOD_DAYS: int = 7  # Количество дней промопериода для новых пользователей

    BOT_SECRET_TOKEN: str

    YOOKASSA_SHOP_ID: str
    YOOKASSA_SECRET_KEY: str
    YOOKASSA_CALLBACK_RETURN_URL: str

    # Admin panel credentials (опционально, по умолчанию admin/admin)
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

    @property
    def access_token_expire_timedelta(self) -> timedelta:
        """access token"""
        return timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)


settings = Settings()
