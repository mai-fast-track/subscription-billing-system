"""
Notification-related Celery tasks
"""

from app.celery_app import celery_app
from app.core.clients.yookassa_client import yookassa_client
from app.core.database import db_manager
from app.core.logger import logger
from app.database.sync_unit_of_work import SyncUnitOfWork

# Логируем импорт модуля
logger.info("[NOTIFICATION MODULE] Module app.tasks.notification imported")


# Условный декоратор для задач Celery
# Если celery_app None, возвращаем функцию как есть (без декоратора)
def task_decorator(*args, **kwargs):
    """Условный декоратор для Celery задач"""
    task_name = kwargs.get("name", "unknown")
    if celery_app is None:
        # Если Celery не инициализирован, возвращаем функцию без декоратора
        logger.warning(f"[NOTIFICATION MODULE] celery_app is None, task {task_name} will not be registered")

        def noop_decorator(func):
            return func

        return noop_decorator
    else:
        # Если Celery инициализирован, применяем декоратор
        logger.info(f"[NOTIFICATION MODULE] Registering task {task_name} with celery_app")
        return celery_app.task(*args, **kwargs)


# Логируем регистрацию задачи
if celery_app:
    logger.info("[NOTIFICATION MODULE] celery_app is available, tasks will be registered")
else:
    logger.error("[NOTIFICATION MODULE] ❌ celery_app is None, cannot register task!")


@task_decorator(
    name="app.tasks.notification.send_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def send_notification(self, user_id: int, message: str, notification_type: str = "info"):
    """
    Отправить уведомление пользователю через Telegram

    Args:
        user_id: ID пользователя
        message: Текст сообщения
        notification_type: Тип уведомления (для логирования)
    """
    if hasattr(self, "request"):
        logger.debug(f"[NOTIFICATION MODULE] Task executed as Celery task: {self.request.id}")
    import os

    pid = os.getpid()
    logger.info(
        f"[NOTIFICATION] ===== TASK STARTED ===== [PID {pid}] user_id={user_id}, type={notification_type}, message_len={len(message) if message else 0}"
    )

    try:
        from app.core.config import settings

        logger.info(
            f"[NOTIFICATION] [PID {pid}] Settings loaded: BOT_TOKEN={'***' if settings.BOT_TOKEN else 'None'}, TELEGRAM_BOT_TOKEN={'***' if settings.TELEGRAM_BOT_TOKEN else 'None'}"
        )
    except Exception as e:
        logger.error(f"[NOTIFICATION] [PID {pid}] Failed to load settings: {e}", exc_info=True)

    try:
        logger.info("[NOTIFICATION] Getting sync session...")
        session = db_manager.get_sync_session()
        logger.info("[NOTIFICATION] Session obtained successfully")

        try:
            logger.info("[NOTIFICATION] Creating SyncUnitOfWork...")
            with SyncUnitOfWork(session, yookassa_client) as uow:
                logger.info(f"[NOTIFICATION] SyncUnitOfWork created, getting user {user_id}...")
                user = uow.users.get_by_id(user_id)

                if not user:
                    logger.warning(f"[NOTIFICATION] User {user_id} not found, cannot send notification")
                    return False

                logger.info(f"[NOTIFICATION] User found: id={user.id}, telegram_id={user.telegram_id}")

                if not user.telegram_id:
                    logger.warning(f"[NOTIFICATION] User {user_id} has no telegram_id, cannot send notification")
                    return False

                logger.info("[NOTIFICATION] Importing telegram_notifier...")
                from app.core.telegram_notifier import telegram_notifier

                logger.info("[NOTIFICATION] telegram_notifier imported successfully")

                logger.info(
                    f"[NOTIFICATION] Sending message to telegram_id={user.telegram_id}, message_length={len(message)}"
                )
                success = telegram_notifier.send_notification_to_user(telegram_id=user.telegram_id, message=message)

                if success:
                    logger.info(
                        f"[NOTIFICATION] Sent successfully to user {user_id} "
                        f"(telegram_id={user.telegram_id}, type={notification_type})"
                    )
                else:
                    logger.warning(
                        f"[NOTIFICATION] Failed to send to user {user_id} "
                        f"(telegram_id={user.telegram_id}, type={notification_type})"
                    )

                return success

        finally:
            logger.info("[NOTIFICATION] Closing session...")
            session.close()
            logger.info("[NOTIFICATION] Session closed")

    except Exception as e:
        logger.error(f"[NOTIFICATION] Error sending notification to user {user_id}: {str(e)}", exc_info=True)
        # Повторяем попытку при ошибке
        raise self.retry(exc=e, countdown=60)


@task_decorator(name="app.tasks.notification.send_payment_notification")
def send_payment_notification(payment_id: int):
    """
    Send payment status notification
    """
    # TODO: Implement payment notification
    # 1. Get payment details
    # 2. Format message based on status
    # 3. Send notification
    pass


@task_decorator(name="app.tasks.notification.send_subscription_notification")
def send_subscription_notification(subscription_id: int, notification_type: str):
    """
    Send subscription status notification
    """
    # TODO: Implement subscription notification
    # 1. Get subscription details
    # 2. Format message based on type (expiring, expired, renewed, etc.)
    # 3. Send notification
    pass


# Проверяем регистрацию задач после импорта модуля
if celery_app:
    try:
        registered_tasks = [name for name in celery_app.tasks.keys() if name.startswith("app.tasks.notification.")]
        if registered_tasks:
            logger.info(f"[NOTIFICATION MODULE] Successfully registered tasks: {', '.join(sorted(registered_tasks))}")
        else:
            logger.warning("[NOTIFICATION MODULE] No notification tasks found in celery_app.tasks!")
    except Exception as e:
        logger.error(f"[NOTIFICATION MODULE] Failed to check task registration: {e}", exc_info=True)
