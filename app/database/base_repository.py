# repository/base.py
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, Generic, Optional, TypeVar

from sqlalchemy import Row, RowMapping, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

T = TypeVar("T", bound=DeclarativeBase)


class BaseRepository(Generic[T], ABC):
    """Base repository с common CRUD operations"""

    def __init__(self, session: AsyncSession) -> None:
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

    async def get_by_id_or_raise(self, id_: int) -> T:
        obj = await self.get_by_id(id_)
        if not obj:
            raise self._get_not_found_exception(id_)
        return obj

    async def get_by_id(self, id_: int) -> Optional[T]:
        """Get by primary key"""
        if id_ < 1:
            return None

        stmt = select(self._model).where(self._model.id == id_)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_by(self, **kwargs: Any) -> Optional[T]:
        """Get single entity by filters"""
        stmt = select(self._model).filter_by(**kwargs)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[Row | RowMapping | Any]:
        """Get all with pagination"""
        stmt = select(self._model).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_all_by(self, **kwargs: Any) -> Sequence[Row | RowMapping | Any]:
        """TODO описание"""
        stmt = select(self._model).filter_by(**kwargs)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def create(self, obj: T) -> T:
        """Create entity"""
        self._session.add(obj)
        await self._session.flush()
        return obj

    async def bulk_create(self, objs: list[T]) -> list[T]:
        """Bulk create"""
        self._session.add_all(objs)
        await self._session.flush()
        return objs

    async def update(self, obj: T) -> T:
        """Update entity"""
        await self._session.merge(obj)
        await self._session.flush()
        return obj

    async def delete(self, obj: T) -> bool:
        """Delete entity"""
        await self._session.delete(obj)
        await self._session.flush()
        return True

    async def count(self, **filters: Any) -> int:
        """Count entities"""
        stmt = select(func.count()).select_from(self._model)
        if filters:
            stmt = stmt.filter_by(**filters)
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def exists(self, **filters: Any) -> bool:
        """Check existence"""
        return await self.count(**filters) > 0
