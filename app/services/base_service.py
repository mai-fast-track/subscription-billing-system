"""
Base service для всех сервисов
"""

from abc import ABC
from typing import Generic, TypeVar

from app.database.unit_of_work import UnitOfWork

T = TypeVar("T")


class BaseService(ABC, Generic[T]):
    """
    Базовый класс для всех сервисов.
    Обеспечивает правильное использование UnitOfWork.
    """

    def __init__(self, uow: UnitOfWork):
        """
        Инициализация сервиса с UnitOfWork.

        Args:
            uow: UnitOfWork для работы с репозиториями
        """
        self.uow = uow
