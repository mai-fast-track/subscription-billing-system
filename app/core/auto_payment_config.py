"""
Сервис для чтения настроек автоплатежей.
Настройки хранятся в Redis по ключу `auto_payment:config` или берутся из settings.
"""

import json
from typing import Optional

from app.core.config import settings
from app.core.logger import logger
from app.core.redis_client import redis_client


class AutoPaymentConfig:
    """Управление настройками автоплатежей - только чтение"""

    REDIS_KEY = "auto_payment:config"

    @classmethod
    def _get_config_from_redis(cls) -> Optional[dict]:
        """Получить настройки из Redis"""
        try:
            config_json = redis_client.client.get(cls.REDIS_KEY)
            if config_json:
                return json.loads(config_json)
        except Exception as e:
            logger.warning(f"Failed to load config from Redis: {e}")
        return None

    @classmethod
    def _get_default_config(cls) -> dict:
        """Получить настройки по умолчанию из settings"""
        return {
            "start_hour": settings.AUTO_PAYMENT_START_HOUR,
            "start_minute": settings.AUTO_PAYMENT_START_MINUTE,
            "end_hour": settings.AUTO_PAYMENT_END_HOUR,
            "end_minute": settings.AUTO_PAYMENT_END_MINUTE,
            "max_attempts": settings.AUTO_PAYMENT_MAX_ATTEMPTS,
            "retry_interval_seconds": settings.AUTO_PAYMENT_RETRY_INTERVAL_SECONDS,
            "redis_ttl_hours": settings.AUTO_PAYMENT_REDIS_TTL_HOURS,
        }

    @classmethod
    def _validate_config(cls, config: dict) -> bool:
        """
        Валидация конфигурации.

        Args:
            config: Словарь с настройками

        Returns:
            True если конфигурация валидна, False иначе
        """
        if not isinstance(config, dict):
            return False

        # Проверяем наличие обязательных ключей
        required_keys = {
            "start_hour",
            "start_minute",
            "end_hour",
            "end_minute",
            "max_attempts",
            "retry_interval_seconds",
            "redis_ttl_hours",
        }

        if not required_keys.issubset(config.keys()):
            logger.warning(f"Config missing required keys: {required_keys - set(config.keys())}")
            return False

        # Валидация значений
        if not (0 <= config.get("start_hour", -1) <= 23):
            return False
        if not (0 <= config.get("start_minute", -1) <= 59):
            return False
        if not (0 <= config.get("end_hour", -1) <= 23):
            return False
        if not (0 <= config.get("end_minute", -1) <= 59):
            return False
        if not (1 <= config.get("max_attempts", 0) <= 10):
            return False
        if not (1 <= config.get("retry_interval_seconds", 0) <= 3600):
            return False
        if not (1 <= config.get("redis_ttl_hours", 0) <= 168):
            return False

        return True

    @classmethod
    def get_config(cls) -> dict:
        """
        Получить текущие настройки (из Redis или settings).
        Всегда читает из Redis при каждом вызове (без кеша).

        Returns:
            dict: Текущие настройки автоплатежей
        """
        # 1. Пытаемся загрузить из Redis
        config = cls._get_config_from_redis()
        if config and cls._validate_config(config):
            return config

        # 2. Fallback на settings
        default_config = cls._get_default_config()
        logger.debug(f"Using default config from settings: {default_config}")
        return default_config


# Глобальный экземпляр
auto_payment_config = AutoPaymentConfig()
