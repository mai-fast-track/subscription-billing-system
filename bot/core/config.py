"""
Bot configuration
"""

from pydantic_settings import BaseSettings


class BotConfig(BaseSettings):
    """Bot configuration"""

    # Telegram Bot
    BOT_TOKEN: str

    # Backend API
    API_BASE_URL: str = "http://api:8000"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


config = BotConfig()
