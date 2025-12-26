"""
Utility functions for Celery tasks with proper async/await handling.

Best practices for running async code in Celery tasks:
1. Create a new event loop for each task (Celery runs in sync context)
2. Properly handle event loop lifecycle
3. Ensure all async resources are cleaned up
4. Handle exceptions properly
5. Use asyncio.run() or properly manage event loop
"""

import asyncio
import logging
from collections.abc import Coroutine
from typing import Any

logger = logging.getLogger(__name__)


def run_async(coro: Coroutine) -> Any:
    """
    Run an async coroutine in a Celery task.

    Best practices:
    - Creates a new event loop for the task
    - Ensures database engine is initialized in this loop
    - Runs the coroutine
    - Properly cleans up the loop
    - Handles all exceptions

    ВАЖНО: asyncpg соединения привязываются к event loop при создании.
    Если engine был создан в другом loop, соединения не будут работать.
    Поэтому мы проверяем и пересоздаем engine в текущем loop, если нужно.

    Args:
        coro: The coroutine to run

    Returns:
        The result of the coroutine

    Raises:
        Exception: Any exception raised by the coroutine
    """
    # Check if there's already an event loop running
    # This shouldn't happen in Celery tasks (they run in sync context)
    try:
        loop = asyncio.get_running_loop()
        # If we're already in an async context, we can't use run_until_complete
        logger.warning("Event loop already running, this shouldn't happen in Celery tasks")
        raise RuntimeError("Cannot run async code in already running event loop")
    except RuntimeError:
        # No event loop running, which is expected in Celery tasks
        pass

    # Create a new event loop for this task
    # Each task gets its own isolated event loop
    loop = None
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # ВАЖНО: asyncpg соединения привязываются к event loop при создании.
        # Если engine был создан в другом loop (например, в worker_process_init),
        # соединения не будут работать в новом loop.
        # Решение: пересоздаем engine в текущем loop, если он уже был создан.
        async def ensure_db_in_current_loop():
            """Убедиться, что БД engine создан в текущем event loop"""
            from app.core.config import settings
            from app.core.database import db_manager, init_database

            # Если engine уже создан, закрываем его и пересоздаем в текущем loop
            # Это гарантирует, что все соединения создаются в правильном loop
            if db_manager.engine is not None:
                logger.debug("Recreating database engine in current event loop")
                await db_manager.close()
                # Сбрасываем engine, чтобы init_database мог его пересоздать
                db_manager.engine = None
                db_manager.async_session_maker = None

            # Инициализируем БД в текущем event loop
            init_database(debug=settings.DEBUG)

        # Убеждаемся, что БД инициализирована в этом loop
        loop.run_until_complete(ensure_db_in_current_loop())

        # Run the coroutine
        return loop.run_until_complete(coro)
    finally:
        # Clean up: cancel any remaining tasks
        if loop is not None:
            try:
                # Get all pending tasks
                pending = asyncio.all_tasks(loop)
                if pending:
                    logger.debug(f"Cancelling {len(pending)} pending tasks")
                    for task in pending:
                        task.cancel()
                    # Wait for cancellation to complete (with timeout)
                    try:
                        loop.run_until_complete(
                            asyncio.wait_for(asyncio.gather(*pending, return_exceptions=True), timeout=5.0)
                        )
                    except asyncio.TimeoutError:
                        logger.warning("Timeout waiting for tasks to cancel")
            except Exception as e:
                logger.warning(f"Error cancelling pending tasks: {e}")
            finally:
                # Close the event loop
                try:
                    loop.close()
                except Exception as e:
                    logger.warning(f"Error closing event loop: {e}")
                finally:
                    # Remove the loop from thread-local storage
                    try:
                        asyncio.set_event_loop(None)
                    except Exception:
                        pass
