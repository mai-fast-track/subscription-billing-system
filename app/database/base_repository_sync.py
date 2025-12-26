# repository/base_sync.py
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, Generic, Optional, TypeVar

from sqlalchemy import Row, RowMapping, func, select
from sqlalchemy.orm import DeclarativeBase, Session

T = TypeVar("T", bound=DeclarativeBase)


class BaseRepositorySync(Generic[T], ABC):
    """Синхронный Base repository с common CRUD operations для Celery"""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._model = self._get_model()

    @abstractmethod
    def _get_model(self) -> type[T]:
        """Вернуть SQLAlchemy модель"""
        pass

    @abstractmethod
    def _get_not_found_exception(self, id_):
        """Вернуть исключение, когда пустой ответ"""
        pass

    def get_by_id_or_raise(self, id_: int) -> T:
        obj = self.get_by_id(id_)
        if not obj:
            raise self._get_not_found_exception(id_)
        return obj

    def get_by_id(self, id_: int) -> Optional[T]:
        """Get by primary key"""
        if id_ < 1:
            return None

        stmt = select(self._model).where(self._model.id == id_)
        result = self._session.execute(stmt)
        return result.scalars().first()

    def get_by(self, **kwargs: Any) -> Optional[T]:
        """Get single entity by filters"""
        stmt = select(self._model).filter_by(**kwargs)
        result = self._session.execute(stmt)
        return result.scalars().first()

    def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[Row | RowMapping | Any]:
        """Get all with pagination"""
        stmt = select(self._model).offset(skip).limit(limit)
        result = self._session.execute(stmt)
        return result.scalars().all()

    def get_all_by(self, **kwargs: Any) -> Sequence[Row | RowMapping | Any]:
        """Get all entities by filters"""
        stmt = select(self._model).filter_by(**kwargs)
        result = self._session.execute(stmt)
        return result.scalars().all()

    def create(self, obj: T) -> T:
        """Create entity"""
        self._session.add(obj)
        self._session.flush()
        return obj

    def bulk_create(self, objs: list[T]) -> list[T]:
        """Bulk create"""
        self._session.add_all(objs)
        self._session.flush()
        return objs

    def update(self, obj: T) -> T:
        """Update entity"""
        self._session.merge(obj)
        self._session.flush()
        return obj

    def delete(self, obj: T) -> bool:
        """Delete entity"""
        self._session.delete(obj)
        self._session.flush()
        return True

    def count(self, **filters: Any) -> int:
        """Count entities"""
        stmt = select(func.count()).select_from(self._model)
        if filters:
            stmt = stmt.filter_by(**filters)
        result = self._session.execute(stmt)
        return result.scalar() or 0

    def exists(self, **filters: Any) -> bool:
        """Check existence"""
        return self.count(**filters) > 0
