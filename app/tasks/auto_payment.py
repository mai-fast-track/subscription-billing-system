"""
Auto Payment Celery tasks - задачи для автоматических платежей.

ВАЖНО: Все задачи полностью синхронные, без async/await.
Используют SyncUnitOfWork и синхронные репозитории.
"""

from datetime import datetime, timezone
from typing import Any

from app.celery_app import celery_app
from app.core.auto_payment_config import auto_payment_config
from app.core.clients.yookassa_client import yookassa_client
from app.core.database import db_manager
from app.core.logger import logger
from app.core.redis_client import redis_client
from app.database.sync_unit_of_work import SyncUnitOfWork
from app.services.auto_payment_service_sync import AutoPaymentServiceSync


# Условный декоратор для задач Celery
# Если celery_app None, возвращаем функцию как есть (без декоратора)
def task_decorator(*args, **kwargs):
    """Условный декоратор для Celery задач"""
    if celery_app is None:
        # Если Celery не инициализирован, возвращаем функцию без декоратора
        def noop_decorator(func):
            return func

        return noop_decorator
    else:
        # Если Celery инициализирован, применяем декоратор
        return celery_app.task(*args, **kwargs)


@task_decorator(
    name="app.tasks.auto_payment.collect_subscriptions_for_payment",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    acks_late=True,
)
def collect_subscriptions_for_payment(self) -> dict[str, Any]:
    """
    Периодическая задача для сбора подписок, которые требуют платежа сегодня.
    Запускается ежедневно в начале дня (по расписанию из конфига).

    Собирает все активные подписки с end_date сегодня, сохраняет их ID в Redis,
    и запускает обработку для каждой подписки отдельной задачей.

    СИНХРОННАЯ задача - использует SyncUnitOfWork и синхронные репозитории.

    Returns:
        Dict с результатами сбора
    """
    session = db_manager.get_sync_session()

    try:
        with SyncUnitOfWork(session, yookassa_client) as uow:
            # Получаем все подписки, которые заканчиваются сегодня
            subscriptions = uow.subscriptions.get_subscriptions_ending_today()

            subscription_ids = [sub.id for sub in subscriptions]

            # Сохраняем в Redis
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            redis_client.add_subscriptions_for_date(subscription_ids, today_str)

            # Запускаем обработку для каждой подписки отдельной задачей
            for subscription_id in subscription_ids:
                process_single_subscription_payment.delay(subscription_id)

            result = {
                "total": len(subscription_ids),
                "collected": len(subscription_ids),
                "date": today_str,
            }

            logger.info(f"Collected {len(subscription_ids)} subscriptions for payment processing: {result}")
            return result

    except Exception as e:
        logger.error(f"Error in collect_subscriptions_for_payment task: {str(e)}", exc_info=True)
        raise self.retry(exc=e, countdown=300)


@task_decorator(
    name="app.tasks.auto_payment.process_single_subscription_payment",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    acks_late=True,
)
def process_single_subscription_payment(self, subscription_id: int) -> dict[str, Any]:
    """
    Обработать платеж для одной подписки.

    Запускается для каждой подписки из collect_subscriptions_for_payment.

    Логика:
    - Если есть saved_payment_method_id: создает платеж и запускает попытки автосписания
    - Если нет saved_payment_method_id: создает платеж со ссылкой, отправляет уведомление, ставит cancelled

    После обработки удаляет subscription_id из Redis.

    СИНХРОННАЯ задача - использует SyncUnitOfWork и синхронные репозитории.

    Args:
        subscription_id: ID подписки для обработки

    Returns:
        Dict с результатом обработки
    """
    session = db_manager.get_sync_session()
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    try:
        with SyncUnitOfWork(session, yookassa_client) as uow:
            service = AutoPaymentServiceSync(uow)
            result = service.process_single_subscription_payment(subscription_id)

            # Если создан платеж для автосписания - запускаем первую попытку
            if result.get("success") and result.get("needs_retry") and result.get("payment_id"):
                retry_auto_payment_attempt.apply_async(args=[result["payment_id"], 1], countdown=0)
                logger.info(f"Scheduled first auto payment attempt for payment {result['payment_id']}")

            # Удаляем из Redis после обработки
            redis_client.remove_subscription(subscription_id, today_str)

            logger.info(f"Processed subscription {subscription_id}: {result}")
            return result

    except Exception as e:
        logger.error(f"Error processing subscription {subscription_id}: {str(e)}", exc_info=True)
        # Удаляем из Redis даже при ошибке, чтобы не застрять
        redis_client.remove_subscription(subscription_id, today_str)
        raise self.retry(exc=e, countdown=300, args=[subscription_id])


@task_decorator(
    name="app.tasks.auto_payment.retry_auto_payment_attempt",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    acks_late=True,
)
def retry_auto_payment_attempt(self, payment_id: int, attempt: int) -> dict[str, Any]:
    """
    Попытка автосписания для платежа.

    Запускается для каждой попытки автосписания (с интервалом из конфига).

    Логика:
    - Делает попытку автосписания через YooKassa
    - При успехе: продлевает подписку, отправляет уведомление
    - При неудаче и attempt < MAX: запускает следующую попытку через apply_async с countdown
    - При неудаче и attempt == MAX: ставит cancelled_waiting, отправляет уведомление

    СИНХРОННАЯ задача - использует SyncUnitOfWork и синхронные репозитории.

    Args:
        payment_id: ID платежа
        attempt: Номер попытки (начинается с 1)

    Returns:
        Dict с результатом попытки
    """
    session = db_manager.get_sync_session()

    try:
        with SyncUnitOfWork(session, yookassa_client) as uow:
            service = AutoPaymentServiceSync(uow)
            result = service.retry_auto_payment_attempt(payment_id, attempt)

            # Если неудача и есть еще попытки - запускаем следующую
            if not result.get("success") and not result.get("final"):
                next_attempt = attempt + 1
                # Получаем настройки из Redis (с fallback на settings)
                config = auto_payment_config.get_config()
                max_attempts = config["max_attempts"]
                retry_interval = config["retry_interval_seconds"]

                if next_attempt <= max_attempts:
                    # Запускаем следующую попытку через интервал
                    retry_auto_payment_attempt.apply_async(args=[payment_id, next_attempt], countdown=retry_interval)
                    logger.info(
                        f"Scheduled next attempt {next_attempt} for payment {payment_id} in {retry_interval} seconds"
                    )

            logger.info(f"Auto payment attempt {attempt} for payment {payment_id}: {result}")
            return result

    except Exception as e:
        logger.error(
            f"Error in retry_auto_payment_attempt for payment {payment_id}, attempt {attempt}: {str(e)}", exc_info=True
        )
        raise self.retry(exc=e, countdown=300, args=[payment_id, attempt])


@task_decorator(
    name="app.tasks.auto_payment.process_cancelled_waiting_subscriptions",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    acks_late=True,
)
def process_cancelled_waiting_subscriptions(self) -> dict[str, Any]:
    """
    Периодическая задача для обработки подписок со статусом cancelled_waiting.
    Запускается ежедневно в конце дня (по расписанию из конфига).

    Переводит все подписки со статусом cancelled_waiting в cancelled.

    СИНХРОННАЯ задача - использует SyncUnitOfWork и синхронные репозитории.

    Returns:
        Dict с результатами обработки
    """
    session = db_manager.get_sync_session()

    try:
        with SyncUnitOfWork(session, yookassa_client) as uow:
            service = AutoPaymentServiceSync(uow)
            result = service.process_cancelled_waiting_subscriptions()

            logger.info(f"Cancelled waiting subscriptions processed: {result}")
            return result

    except Exception as e:
        logger.error(f"Error in process_cancelled_waiting_subscriptions task: {str(e)}", exc_info=True)
        raise self.retry(exc=e, countdown=300)


@task_decorator(
    name="app.tasks.auto_payment.send_payment_reminders",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    acks_late=True,
)
def send_payment_reminders(self) -> dict[str, Any]:
    """
    Периодическая задача для отправки уведомлений пользователям о предстоящем платеже завтра.
    Запускается ежедневно в 01:00 по расписанию.

    СИНХРОННАЯ задача - использует SyncUnitOfWork и синхронные репозитории.

    Returns:
        Dict с результатами отправки
    """
    session = db_manager.get_sync_session()

    try:
        with SyncUnitOfWork(session, yookassa_client) as uow:
            service = AutoPaymentServiceSync(uow)
            result = service.send_payment_reminder_notifications()
            logger.info(f"Payment reminders sent: {result}")
            return result
    except Exception as e:
        logger.error(f"Error in send_payment_reminders task: {str(e)}", exc_info=True)
        raise self.retry(exc=e, countdown=300)
