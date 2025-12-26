import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.core.config import config
from bot.handlers.user import user_router


logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", stream=sys.stdout, force=True
)
logger = logging.getLogger(__name__)


class BotManager:
    """Менеджер для управления ботом"""

    def __init__(self):
        self.bot = None
        self.dp = None

    async def initialize(self):
        logger.info("🚀 Инициализация бота...")


        logger.info("🤖 Создаём Bot и Dispatcher...")
        try:
            self.bot = Bot(token=config.BOT_TOKEN)
            logger.info("✅ Bot создан")
        except Exception as e:
            logger.error(f"❌ ОШИБКА при создании Bot: {e}", exc_info=True)
            raise

        try:
            storage = MemoryStorage()
            self.dp = Dispatcher(storage=storage)
            logger.info("✅ Dispatcher создан")
        except Exception as e:
            logger.error(f"❌ ОШИБКА при создании Dispatcher: {e}", exc_info=True)
            raise

        logger.info("📌 Регистрируем handlers...")
        try:
            self._register_handlers()
            logger.info("✅ Handlers зарегистрированы")
        except Exception as e:
            logger.error(f"❌ ОШИБКА при регистрации handlers: {e}", exc_info=True)
            raise

        logger.info("✅ Бот полностью готов!")

    def _register_handlers(self):
        """Регистрировать handlers"""
        logger.info("📝 Регистрация handlers...")
        self.dp.include_router(user_router)
        logger.info("✅ Handlers зарегистрированы")

    async def start_polling(self):
        """Запустить polling"""
        logger.info("🔄 Запуск polling...")
        try:
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"❌ ОШИБКА при polling: {e}", exc_info=True)
            raise
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Завершить работу бота"""
        logger.info("🛑 Завершение работы...")
        if self.bot:
            await self.bot.session.close()
        logger.info("✅ Бот остановлен")


async def main():
    """Главная функция"""
    logger.info("=" * 60)
    logger.info("ЗАПУСК БОТА")
    logger.info("=" * 60)
    logger.info(f"API Base URL: {config.API_BASE_URL}")

    try:
        manager = BotManager()
        logger.info("✅ BotManager создан")

        await manager.initialize()
        logger.info("✅ Инициализация завершена, запускаем polling...")

        await manager.start_polling()
    except KeyboardInterrupt:
        logger.info("⌨️ Бот остановлен пользователем (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    logger.info("🚀 ТОЧКА ВХОДА MAIN")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⌨️ Программа остановлена")
    except Exception as e:
        logger.error(f"❌ НЕОБРАБОТАННОЕ ИСКЛЮЧЕНИЕ: {e}", exc_info=True)
        sys.exit(1)
