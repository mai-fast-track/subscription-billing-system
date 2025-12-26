import logging

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base для всех моделей"""

    pass


class DatabaseManager:
    """
    Менеджер для управления БД соединениями.

    Важно: get_session() только создаёт сессию!
    Коммит/откат - это ответственность UoW.
    """

    def __init__(self):
        self.engine = None
        self.async_session_maker = None
        # Синхронный engine для Celery
        self.sync_engine = None
        self.sync_session_maker = None

    def init_engine(self, database_url: str = None, debug: bool = False):
        """
        Инициализировать engine (вызывается один раз при старте).
        Настройки пула:
        - pool_size=20: Размер пула для каждого процесса (FastAPI или worker)
        - max_overflow=10: Дополнительные соединения при пиковой нагрузке
        - pool_pre_ping=True: Проверка соединений перед использованием (важно для долгих idle соединений)
        - pool_recycle=3600: Пересоздание соединений каждый час (предотвращает проблемы с таймаутами БД)
        """
        if self.engine is not None:
            logger.warning("Engine already initialized")
            return

        if not database_url:
            from app.core.config import settings

            database_url = settings.DATABASE_URL

        if not database_url:
            raise ValueError("DATABASE_URL не установлена")

        self.engine = create_async_engine(
            database_url,
            echo=debug,
            poolclass=QueuePool,
            pool_size=20,  # Размер пула для каждого процесса
            max_overflow=10,  # Дополнительные соединения при нагрузке
            pool_pre_ping=True,  # Проверяет соединения перед использованием
            pool_recycle=3600,  # Пересоздавать каждый час (предотвращает таймауты БД)
            future=True,
        )

        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        logger.info("Database engine initialized successfully")

    def init_sync_engine(self, database_url: str = None, debug: bool = False):
        """
        Инициализировать синхронный engine для Celery (вызывается один раз при старте worker).
        Настройки пула:
        - pool_size=5: Размер пула для каждого worker процесса
        - max_overflow=10: Дополнительные соединения при пиковой нагрузке
        - pool_pre_ping=True: Проверка соединений перед использованием
        - pool_recycle=3600: Пересоздание соединений каждый час
        """
        if self.sync_engine is not None:
            logger.warning("Sync engine already initialized")
            return

        if not database_url:
            from app.core.config import settings

            database_url = settings.DATABASE_URL

        if not database_url:
            raise ValueError("DATABASE_URL не установлена")

        sync_url = database_url.replace("+asyncpg", "+psycopg2").replace("postgresql+asyncpg://", "postgresql://")

        self.sync_engine = create_engine(
            sync_url,
            echo=debug,
            poolclass=QueuePool,
            pool_size=5,  # Размер пула для каждого worker процесса
            max_overflow=10,  # Дополнительные соединения при нагрузке
            pool_pre_ping=True,  # Проверяет соединения перед использованием
            pool_recycle=3600,  # Пересоздавать каждый час
        )

        self.sync_session_maker = sessionmaker(
            bind=self.sync_engine,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        logger.info("Sync database engine initialized successfully for Celery")

    def get_sync_session(self) -> Session:
        """
        Получить новую синхронную сессию для Celery задач.
        """
        if self.sync_session_maker is None:
            logger.warning(
                "Sync database not initialized when get_sync_session() called. "
                "This should not happen if worker_process_init signal fired correctly. "
                "Attempting automatic initialization..."
            )

            try:
                self.init_sync_engine()
                logger.info("Sync database auto-initialized in get_sync_session()")
            except Exception as e:
                logger.error(f"Failed to auto-initialize sync database: {e}", exc_info=True)
                raise RuntimeError(
                    "Sync database not initialized. Did you call init_sync_engine()? "
                    f"Auto-initialization also failed: {e}"
                )

        if self.sync_session_maker is None:
            raise RuntimeError("Sync database not initialized. Did you call init_sync_engine()?")

        # Просто создаём новую сессию и возвращаем
        # Коммит/откат будет делать SyncUnitOfWork
        session = self.sync_session_maker()
        return session

    async def close(self):
        """Закрыть соединения при shutdown"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")

    async def get_session(self) -> AsyncSession:
        """
        Получить новую сессию для запроса.
        """
        if self.async_session_maker is None:
            logger.warning(
                "Database not initialized when get_session() called. "
                "This should not happen if worker_process_init signal fired correctly. "
                "Attempting automatic initialization..."
            )

            # Пытаемся инициализировать автоматически
            # Это безопасно, так как init_engine проверяет, не инициализирована ли БД
            try:
                init_database()
                logger.info("Database auto-initialized in get_session()")
            except Exception as e:
                logger.error(f"Failed to auto-initialize database: {e}", exc_info=True)
                raise RuntimeError(
                    f"Database not initialized. Did you call init_engine()? Auto-initialization also failed: {e}"
                )

        if self.async_session_maker is None:
            raise RuntimeError("Database not initialized. Did you call init_engine()?")


        session = self.async_session_maker()
        return session

    async def init_db(self):
        """Инициализировать БД - создать таблицы"""
        from app.models import (  # noqa: F401
            Payment,
            Promotion,
            Subscription,
            SubscriptionPlan,
            User,
            UserPromotionUsage,
        )

        if self.engine is None:
            logger.warning("Engine not initialized. Call init_engine() first.")
            return

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")


db_manager = DatabaseManager()


def init_database(debug: bool = False):
    """
    Инициализировать базу данных.
    Используется как в FastAPI, так и в Celery worker.
    """
    if db_manager.engine is not None:
        logger.warning("Database engine already initialized")
        return

    from app.core.config import settings

    db_manager.init_engine(debug=debug or settings.DEBUG)
    logger.info("Database engine initialized")


async def get_db():
    """
    FastAPI dependency для получения сессии БД.
    Используется для обратной совместимости, но рекомендуется использовать get_uow.
    """
    session = await db_manager.get_session()
    try:
        yield session
    finally:
        await session.close()


async def get_uow():
    """
    FastAPI dependency для получения UnitOfWork.
    Правильный способ работы с БД через UoW паттерн.
    """
    from app.core.clients.yookassa_client import yookassa_client
    from app.database.unit_of_work import UnitOfWork

    session = await db_manager.get_session()
    uow = UnitOfWork(session, yookassa_client)
    try:
        yield uow
    finally:
        # UoW сам управляет commit/rollback в __aexit__
        # Но нужно закрыть сессию, если UoW не использовался как контекстный менеджер
        await uow.close()
