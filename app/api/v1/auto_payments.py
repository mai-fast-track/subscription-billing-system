"""
Auto Payment endpoints - эндпоинты для тестирования и мониторинга автоплатежей
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_uow
from app.core.logger import logger
from app.core.redis_client import redis_client
from app.database.unit_of_work import UnitOfWork
from app.services.auto_payment_service import AutoPaymentService

router = APIRouter(prefix="/auto-payments", tags=["auto-payments"])


@router.post("/process-today", response_model=dict[str, Any])
async def process_auto_payments_today():
    """
    Ручной запуск обработки автоплатежей для подписок, заканчивающихся сегодня.
    Использует новую архитектуру - запускает Celery задачу collect_subscriptions_for_payment.
    Полезно для тестирования.

    POST /api/v1/auto-payments/process-today

    Returns:
        Dict с task_id и результатом
    """
    try:
        from app.celery_app import celery_app

        if celery_app is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Celery не инициализирован. Проверьте настройки Redis и CELERY_BROKER_URL.",
            )

        from app.tasks.auto_payment import collect_subscriptions_for_payment

        # Запускаем задачу асинхронно (новая архитектура)
        task = collect_subscriptions_for_payment.delay()

        if task is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось запустить задачу Celery. Проверьте подключение к Redis и статус Celery worker.",
            )

        return {
            "success": True,
            "task_id": task.id,
            "message": "Collection task started (new architecture)",
            "note": "This uses the new architecture with Redis coordination",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting auto payments task: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка запуска задачи: {str(e)}"
        )


@router.post("/send-reminders", response_model=dict[str, Any])
async def send_payment_reminders(uow: UnitOfWork = Depends(get_uow)):
    """
    Ручной запуск отправки напоминаний о предстоящих платежах.
    Полезно для тестирования.

    POST /api/v1/auto-payments/send-reminders

    Returns:
        Dict с результатами отправки
    """
    async with uow:
        try:
            service = AutoPaymentService(uow)
            result = await service.send_payment_reminder_notifications()
            return result
        except Exception as e:
            logger.error(f"Error sending reminders: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка отправки напоминаний: {str(e)}"
            )


@router.get("/subscriptions-ending-today", response_model=list[dict[str, Any]])
async def get_subscriptions_ending_today(uow: UnitOfWork = Depends(get_uow)):
    """
    Получить список подписок, которые заканчиваются сегодня.
    Полезно для проверки перед запуском автоплатежей.

    GET /api/v1/auto-payments/subscriptions-ending-today

    Returns:
        List подписок с информацией
    """
    async with uow:
        try:
            subscriptions = await uow.subscriptions.get_subscriptions_ending_today()

            result = []
            for sub in subscriptions:
                user = await uow.users.get_by_id(sub.user_id)
                plan = await uow.subscription_plans.get_by_id(sub.plan_id)

                result.append(
                    {
                        "subscription_id": sub.id,
                        "user_id": sub.user_id,
                        "user_telegram_id": user.telegram_id if user else None,
                        "plan_id": sub.plan_id,
                        "plan_name": plan.name if plan else None,
                        "plan_price": plan.price if plan else None,
                        "status": sub.status,
                        "start_date": sub.start_date.isoformat() if sub.start_date else None,
                        "end_date": sub.end_date.isoformat() if sub.end_date else None,
                        "has_saved_payment_method": user.saved_payment_method_id is not None if user else False,
                    }
                )

            return result
        except Exception as e:
            logger.error(f"Error getting subscriptions ending today: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка получения подписок: {str(e)}"
            )


@router.get("/subscriptions-ending-tomorrow", response_model=list[dict[str, Any]])
async def get_subscriptions_ending_tomorrow(uow: UnitOfWork = Depends(get_uow)):
    """
    Получить список подписок, которые заканчиваются завтра.
    Полезно для проверки перед отправкой напоминаний.

    GET /api/v1/auto-payments/subscriptions-ending-tomorrow

    Returns:
        List подписок с информацией
    """
    async with uow:
        try:
            subscriptions = await uow.subscriptions.get_subscriptions_ending_tomorrow()

            result = []
            for sub in subscriptions:
                user = await uow.users.get_by_id(sub.user_id)
                plan = await uow.subscription_plans.get_by_id(sub.plan_id)

                result.append(
                    {
                        "subscription_id": sub.id,
                        "user_id": sub.user_id,
                        "user_telegram_id": user.telegram_id if user else None,
                        "plan_id": sub.plan_id,
                        "plan_name": plan.name if plan else None,
                        "plan_price": plan.price if plan else None,
                        "status": sub.status,
                        "start_date": sub.start_date.isoformat() if sub.start_date else None,
                        "end_date": sub.end_date.isoformat() if sub.end_date else None,
                        "has_saved_payment_method": user.saved_payment_method_id is not None if user else False,
                    }
                )

            return result
        except Exception as e:
            logger.error(f"Error getting subscriptions ending tomorrow: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка получения подписок: {str(e)}"
            )


@router.post("/test-subscription/{subscription_id}", response_model=dict[str, Any])
async def test_auto_payment_for_subscription(subscription_id: int, uow: UnitOfWork = Depends(get_uow)):
    """
    Протестировать автоплатеж для конкретной подписки.
    Полезно для отладки.

    POST /api/v1/auto-payments/test-subscription/{subscription_id}

    Args:
        subscription_id: ID подписки для тестирования

    Returns:
        Dict с результатом тестирования
    """
    async with uow:
        try:
            subscription = await uow.subscriptions.get_by_id_or_raise(subscription_id)
            service = AutoPaymentService(uow)

            result = await service._process_single_auto_payment(subscription)
            return result
        except Exception as e:
            logger.error(f"Error testing auto payment for subscription {subscription_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка тестирования автоплатежа: {str(e)}"
            )


@router.get("/stats", response_model=dict[str, Any])
async def get_auto_payment_stats(uow: UnitOfWork = Depends(get_uow)):
    """
    Получить статистику по автоплатежам.

    GET /api/v1/auto-payments/stats

    Returns:
        Dict со статистикой
    """
    async with uow:
        try:
            from datetime import datetime, timedelta

            from sqlalchemy import and_, func, select

            from app.core.enums import PaymentStatus
            from app.models import Payment

            # Подписки, заканчивающиеся сегодня
            subscriptions_today = await uow.subscriptions.get_subscriptions_ending_today()

            # Подписки, заканчивающиеся завтра
            subscriptions_tomorrow = await uow.subscriptions.get_subscriptions_ending_tomorrow()

            # Статистика по автоплатежам за последние 30 дней
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
            stmt = select(
                func.count(Payment.id).label("total"),
                func.sum(func.case((Payment.status == PaymentStatus.succeeded.value, 1), else_=0)).label("succeeded"),
                func.sum(func.case((Payment.status == PaymentStatus.failed.value, 1), else_=0)).label("failed"),
                func.sum(func.case((Payment.status == PaymentStatus.pending.value, 1), else_=0)).label("pending"),
            ).where(and_(Payment.payment_method == "auto_payment", Payment.created_at >= thirty_days_ago))

            result = await uow.session.execute(stmt)
            stats_row = result.first()

            # Пользователи с сохраненными платежными методами
            from app.models import User

            stmt_users = select(func.count(User.id)).where(User.saved_payment_method_id.isnot(None))
            result_users = await uow.session.execute(stmt_users)
            users_with_payment_method = result_users.scalar() or 0

            return {
                "subscriptions_ending_today": len(subscriptions_today),
                "subscriptions_ending_tomorrow": len(subscriptions_tomorrow),
                "users_with_saved_payment_method": users_with_payment_method,
                "auto_payments_last_30_days": {
                    "total": stats_row.total or 0,
                    "succeeded": stats_row.succeeded or 0,
                    "failed": stats_row.failed or 0,
                    "pending": stats_row.pending or 0,
                    "success_rate": (
                        (stats_row.succeeded or 0) / (stats_row.total or 1) * 100 if stats_row.total else 0
                    ),
                },
            }
        except Exception as e:
            logger.error(f"Error getting auto payment stats: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка получения статистики: {str(e)}"
            )


@router.post("/simulate-subscription-ending/{subscription_id}", response_model=dict[str, Any])
async def simulate_subscription_ending(subscription_id: int, uow: UnitOfWork = Depends(get_uow)):
    """
    Симулировать окончание подписки (установить end_date на сегодня).
    Полезно для тестирования автоплатежей без ожидания реального окончания.

    POST /api/v1/auto-payments/simulate-subscription-ending/{subscription_id}

    Args:
        subscription_id: ID подписки

    Returns:
        Dict с результатом
    """
    async with uow:
        try:
            subscription = await uow.subscriptions.get_by_id_or_raise(subscription_id)

            # Устанавливаем end_date на сегодня
            today = datetime.now(timezone.utc).replace(hour=23, minute=59, second=59)
            subscription.end_date = today
            subscription.updated_at = datetime.now(timezone.utc)

            await uow.subscriptions.update(subscription)

            return {
                "success": True,
                "message": f"Subscription {subscription_id} end_date set to today",
                "new_end_date": subscription.end_date.isoformat(),
            }
        except Exception as e:
            logger.error(f"Error simulating subscription ending: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка симуляции: {str(e)}")


# Новые эндпоинты для тестирования новой архитектуры


@router.post("/collect-subscriptions", response_model=dict[str, Any])
async def collect_subscriptions_for_payment():
    """
    Ручной запуск сбора подписок для обработки (новая архитектура).
    Запускает Celery задачу collect_subscriptions_for_payment.

    POST /api/v1/auto-payments/collect-subscriptions

    Returns:
        Dict с task_id и результатом
    """
    try:
        from app.celery_app import celery_app

        if celery_app is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Celery не инициализирован. Проверьте настройки Redis и CELERY_BROKER_URL.",
            )

        from app.tasks.auto_payment import collect_subscriptions_for_payment

        # Запускаем задачу асинхронно
        task = collect_subscriptions_for_payment.delay()

        if task is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось запустить задачу Celery. Проверьте подключение к Redis и статус Celery worker.",
            )

        return {
            "success": True,
            "task_id": task.id,
            "message": "Collection task started",
            "check_status": f"/api/v1/auto-payments/task-status/{task.id}",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting collection task: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка запуска задачи: {str(e)}"
        )


@router.post("/process-subscription/{subscription_id}", response_model=dict[str, Any])
async def process_single_subscription(subscription_id: int):
    """
    Ручной запуск обработки одной подписки (новая архитектура).
    Запускает Celery задачу process_single_subscription_payment.

    POST /api/v1/auto-payments/process-subscription/{subscription_id}

    Args:
        subscription_id: ID подписки для обработки

    Returns:
        Dict с task_id
    """
    try:
        from app.celery_app import celery_app
        from app.core.config import settings

        logger.info(
            f"Checking Celery initialization: CELERY_BROKER_URL={settings.CELERY_BROKER_URL}, "
            f"CELERY_RESULT_BACKEND={settings.CELERY_RESULT_BACKEND}, celery_app={celery_app is not None}"
        )

        if celery_app is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Celery не инициализирован. CELERY_BROKER_URL={settings.CELERY_BROKER_URL}, "
                f"CELERY_RESULT_BACKEND={settings.CELERY_RESULT_BACKEND}. "
                f"Проверьте настройки Redis и переменные окружения.",
            )

        from app.tasks.auto_payment import process_single_subscription_payment

        task = process_single_subscription_payment.delay(subscription_id)

        if task is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось запустить задачу Celery. Проверьте подключение к Redis и статус Celery worker.",
            )

        return {
            "success": True,
            "task_id": task.id,
            "subscription_id": subscription_id,
            "message": "Processing task started",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting processing task: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка запуска задачи: {str(e)}"
        )


@router.post("/retry-payment/{payment_id}/{attempt}", response_model=dict[str, Any])
async def retry_auto_payment(payment_id: int, attempt: int):
    """
    Ручной запуск попытки автосписания (новая архитектура).
    Запускает Celery задачу retry_auto_payment_attempt.

    POST /api/v1/auto-payments/retry-payment/{payment_id}/{attempt}

    Args:
        payment_id: ID платежа
        attempt: Номер попытки (начинается с 1)

    Returns:
        Dict с task_id
    """
    try:
        from app.celery_app import celery_app

        if celery_app is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Celery не инициализирован. Проверьте настройки Redis и CELERY_BROKER_URL.",
            )

        from app.tasks.auto_payment import retry_auto_payment_attempt

        task = retry_auto_payment_attempt.delay(payment_id, attempt)

        if task is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось запустить задачу Celery. Проверьте подключение к Redis и статус Celery worker.",
            )

        return {
            "success": True,
            "task_id": task.id,
            "payment_id": payment_id,
            "attempt": attempt,
            "message": "Retry task started",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting retry task: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка запуска задачи: {str(e)}"
        )


@router.post("/process-cancelled-waiting", response_model=dict[str, Any])
async def process_cancelled_waiting():
    """
    Ручной запуск обработки cancelled_waiting подписок (новая архитектура).
    Запускает Celery задачу process_cancelled_waiting_subscriptions.

    POST /api/v1/auto-payments/process-cancelled-waiting

    Returns:
        Dict с task_id
    """
    try:
        from app.celery_app import celery_app

        if celery_app is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Celery не инициализирован. Проверьте настройки Redis и CELERY_BROKER_URL.",
            )

        from app.tasks.auto_payment import process_cancelled_waiting_subscriptions

        task = process_cancelled_waiting_subscriptions.delay()

        if task is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось запустить задачу Celery. Проверьте подключение к Redis и статус Celery worker.",
            )

        return {"success": True, "task_id": task.id, "message": "Cancelled waiting processing task started"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting cancelled waiting task: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка запуска задачи: {str(e)}"
        )


@router.get("/redis-status", response_model=dict[str, Any])
async def get_redis_status():
    """
    Получить статус Redis для автосписаний.
    Показывает подписки в Redis на сегодня.

    GET /api/v1/auto-payments/redis-status

    Returns:
        Dict со статусом Redis
    """
    try:
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        subscription_ids = redis_client.get_subscriptions_for_date(today_str)
        count = redis_client.get_subscriptions_count(today_str)

        return {"date": today_str, "subscription_ids": list(subscription_ids), "count": count, "redis_available": True}
    except Exception as e:
        logger.error(f"Error getting Redis status: {str(e)}")
        return {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "subscription_ids": [],
            "count": 0,
            "redis_available": False,
            "error": str(e),
        }


@router.get("/cancelled-waiting", response_model=list[dict[str, Any]])
async def get_cancelled_waiting_subscriptions(uow: UnitOfWork = Depends(get_uow)):
    """
    Получить список подписок со статусом cancelled_waiting.

    GET /api/v1/auto-payments/cancelled-waiting

    Returns:
        List подписок
    """
    async with uow:
        try:
            from app.core.clients.yookassa_client import yookassa_client

            # Используем синхронный репозиторий через sync session
            from app.core.database import db_manager
            from app.core.enums import SubscriptionStatus
            from app.database.sync_unit_of_work import SyncUnitOfWork

            session = db_manager.get_sync_session()
            sync_uow = SyncUnitOfWork(session, yookassa_client)

            try:
                subscriptions = sync_uow.subscriptions.get_subscriptions_by_status(
                    SubscriptionStatus.cancelled_waiting.value
                )

                result = []
                for sub in subscriptions:
                    user = sync_uow.users.get_by_id(sub.user_id)
                    plan = sync_uow.subscription_plans.get_by_id(sub.plan_id)

                    result.append(
                        {
                            "subscription_id": sub.id,
                            "user_id": sub.user_id,
                            "user_telegram_id": user.telegram_id if user else None,
                            "plan_id": sub.plan_id,
                            "plan_name": plan.name if plan else None,
                            "plan_price": plan.price if plan else None,
                            "status": sub.status,
                            "end_date": sub.end_date.isoformat() if sub.end_date else None,
                            "updated_at": sub.updated_at.isoformat() if sub.updated_at else None,
                        }
                    )

                return result
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Error getting cancelled_waiting subscriptions: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка получения подписок: {str(e)}"
            )


# Endpoints для управления настройками автоплатежей


@router.get("/config", response_model=dict[str, Any])
async def get_auto_payment_config():
    """
    Получить текущие настройки автоплатежей.

    GET /api/v1/auto-payments/config

    Returns:
        Dict с текущими настройками
    """
    try:
        from app.core.auto_payment_config import auto_payment_config

        return auto_payment_config.get_config()
    except Exception as e:
        logger.error(f"Error getting auto payment config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка получения настроек: {str(e)}"
        )
