from typing import Optional

import redis

from app.core.config import settings
from app.core.logger import logger


class RedisClient:
    """Redis client для автосписаний"""

    def __init__(self):
        self._client: Optional[redis.Redis] = None

    @property
    def client(self) -> redis.Redis:
        """Получить/создать Redis client"""
        if self._client is None:
            try:
                self._client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                self._client.ping()
                logger.info("Redis client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Redis client: {e}")
                raise
        return self._client

    def _get_subscriptions_key(self, date: str) -> str:
        """Получить ключ Redis для набора подписок"""
        return f"auto_payment:subscriptions:{date}"

    def add_subscriptions_for_date(self, subscription_ids: list[int], date: str) -> bool:
        """
        Добавить ID подписок для даты

        Args:
            subscription_ids: Список ID подписок
            date: Дата в формате YYYY-MM-DD

        Returns:
            True если успешно
        """
        try:
            key = self._get_subscriptions_key(date)
            if subscription_ids:
                ids_str = [str(sid) for sid in subscription_ids]
                self.client.sadd(key, *ids_str)
                ttl_seconds = settings.AUTO_PAYMENT_REDIS_TTL_HOURS * 3600
                self.client.expire(key, ttl_seconds)
                logger.info(f"Added {len(subscription_ids)} subscriptions to Redis key {key}")
            return True
        except Exception as e:
            logger.error(f"Error adding subscriptions to Redis: {e}", exc_info=True)
            return False

    def get_subscriptions_for_date(self, date: str) -> set[int]:
        """
        Получить ID подписок из Redis для указанной даты

        Args:
            date: Дата в формате YYYY-MM-DD

        Returns:
            Множество ID подписок
        """
        try:
            key = self._get_subscriptions_key(date)
            ids_str = self.client.smembers(key)
            return {int(sid) for sid in ids_str}
        except Exception as e:
            logger.error(f"Error getting subscriptions from Redis: {e}", exc_info=True)
            return set()

    def remove_subscription(self, subscription_id: int, date: str) -> bool:
        """
        Удалить ID подписки из Redis

        Args:
            subscription_id: ID подписки для удаления
            date: Дата в формате YYYY-MM-DD

        Returns:
            True если удалено, False если не найдено
        """
        try:
            key = self._get_subscriptions_key(date)
            removed = self.client.srem(key, str(subscription_id))
            return removed > 0
        except Exception as e:
            logger.error(f"Error removing subscription from Redis: {e}", exc_info=True)
            return False

    def get_subscriptions_count(self, date: str) -> int:
        """
        Получить количество подписок в Redis для указанной даты

        Args:
            date: Дата в формате YYYY-MM-DD

        Returns:
            Количество подписок
        """
        try:
            key = self._get_subscriptions_key(date)
            return self.client.scard(key)
        except Exception as e:
            logger.error(f"Error getting subscriptions count from Redis: {e}", exc_info=True)
            return 0

    def clear_subscriptions_for_date(self, date: str) -> bool:
        """
        Очистить все подписки для указанной даты

        Args:
            date: Дата в формате YYYY-MM-DD

        Returns:
            True если успешно
        """
        try:
            key = self._get_subscriptions_key(date)
            deleted = self.client.delete(key)
            return deleted > 0
        except Exception as e:
            logger.error(f"Error clearing subscriptions from Redis: {e}", exc_info=True)
            return False


redis_client = RedisClient()
