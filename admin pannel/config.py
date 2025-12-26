"""
Конфигурация админ-панели
"""

import os

import httpx

from billing_core_api_client import Client

# Определяем API URL
# Приоритет: переменная окружения > проверка Docker > localhost
if "API_URL" in os.environ:
    API_URL = os.getenv("API_URL")
elif os.path.exists("/.dockerenv") or os.getenv("DOCKER_ENV"):
    # В Docker используем имя сервиса
    API_URL = "http://api:8000"
else:
    # Локальный запуск
    API_URL = "http://localhost:8000"


def get_client() -> Client:
    """
    Получить клиент для API.
    Создает новый экземпляр клиента для каждого вызова.

    Returns:
        Client: Настроенный клиент для работы с API
    """
    timeout = httpx.Timeout(30.0, read=60.0)
    return Client(
        base_url=API_URL,
        timeout=timeout,
    )
