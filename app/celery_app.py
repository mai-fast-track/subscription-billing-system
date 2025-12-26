"""
Celery application configuration
Note: Celery is optional and will only initialize if Redis is available
"""

from typing import Optional

from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_process_init, worker_process_shutdown

from app.core.config import settings
from app.core.logger import logger

# Celery app - will be None if Redis is not configured
celery_app: Optional[Celery] = None

# Initialize Celery only if Redis is configured
if settings.CELERY_BROKER_URL and settings.CELERY_RESULT_BACKEND:
    try:
        logger.info(
            f"Initializing Celery with broker={settings.CELERY_BROKER_URL}, backend={settings.CELERY_RESULT_BACKEND}"
        )
        celery_app = Celery(
            "billing_core",
            broker=settings.CELERY_BROKER_URL,
            backend=settings.CELERY_RESULT_BACKEND,
            include=[
                "app.tasks.auto_payment",
                "app.tasks.payment",
                "app.tasks.subscription",
                "app.tasks.notification",
            ],
        )

        celery_app.conf.update(
            task_serializer="json",
            accept_content=["json"],
            result_serializer="json",
            timezone="UTC",
            enable_utc=True,
            broker_connection_retry_on_startup=True,
            beat_schedule={
                "check-expiring-subscriptions": {
                    "task": "app.tasks.subscription.check_expiring_subscriptions",
                    "schedule": 3600.0,  # Every hour
                },
                "process-expired-subscriptions": {
                    "task": "app.tasks.subscription.process_expired_subscriptions",
                    "schedule": 3600.0,  # Every hour
                },
                "collect-subscriptions-for-payment": {
                    "task": "app.tasks.auto_payment.collect_subscriptions_for_payment",
                    "schedule": crontab(
                        hour=settings.AUTO_PAYMENT_START_HOUR, minute=settings.AUTO_PAYMENT_START_MINUTE
                    ),
                },
                "send-payment-reminders": {
                    "task": "app.tasks.auto_payment.send_payment_reminders",
                    "schedule": crontab(hour=1, minute=0),  # Каждый день в 01:00
                },
                "process-cancelled-waiting-subscriptions": {
                    "task": "app.tasks.auto_payment.process_cancelled_waiting_subscriptions",
                    "schedule": crontab(hour=settings.AUTO_PAYMENT_END_HOUR, minute=settings.AUTO_PAYMENT_END_MINUTE),
                },
            },
        )

        # Импортируем все задачи для регистрации после инициализации
        logger.info("Importing Celery task modules...")
        try:
            import app.tasks.auto_payment  # noqa: F401

            logger.info("✓ app.tasks.auto_payment imported")
        except Exception as e:
            logger.error(f"✗ Failed to import app.tasks.auto_payment: {e}", exc_info=True)

        try:
            import app.tasks.notification  # noqa: F401

            logger.info("✓ app.tasks.notification imported")
        except Exception as e:
            logger.error(f"✗ Failed to import app.tasks.notification: {e}", exc_info=True)

        try:
            import app.tasks.payment  # noqa: F401

            logger.info("✓ app.tasks.payment imported")
        except Exception as e:
            logger.error(f"✗ Failed to import app.tasks.payment: {e}", exc_info=True)

        try:
            import app.tasks.subscription  # noqa: F401

            logger.info("✓ app.tasks.subscription imported")
        except Exception as e:
            logger.error(f"✗ Failed to import app.tasks.subscription: {e}", exc_info=True)

        # Проверяем зарегистрированные задачи
        try:
            registered_tasks = list(celery_app.tasks.keys())
            logger.info(
                f"Registered Celery tasks at init time ({len(registered_tasks)}): {', '.join(sorted(registered_tasks))}"
            )
        except Exception as e:
            logger.error(f"Failed to list registered tasks at init time: {e}", exc_info=True)

        logger.info("Celery initialized successfully")

        # Инициализация базы данных при старте worker процесса
        # ВАЖНО: Этот сигнал срабатывает ПОСЛЕ fork, в каждом worker процессе отдельно
        # Type guard: celery_app точно не None здесь, так как мы только что его создали

        @worker_process_init.connect
        def init_worker_process(sender=None, **kwargs):
            """
            Инициализировать базу данных и YooKassa при старте worker процесса.

            Этот сигнал срабатывает ПОСЛЕ того, как worker процесс был форкнут,
            но ДО того, как задачи начнут выполняться. Каждый worker процесс
            получает свой собственный вызов этого сигнала.

            Инициализируем синхронный engine для Celery задач и конфигурируем YooKassa SDK.
            """
            import os

            from app.core.config import settings
            from app.core.database import db_manager
            from app.core.logger import logger
            from app.core.yookassa_manager import yookassa_manager

            pid = os.getpid()
            logger.info(f"[PID {pid}] worker_process_init signal received")

            # Проверяем, что настройки доступны в воркере
            try:
                logger.info(
                    f"[PID {pid}] Settings check: CELERY_BROKER_URL={settings.CELERY_BROKER_URL}, BOT_TOKEN={'***' if settings.BOT_TOKEN else 'None'}"
                )
            except Exception as e:
                logger.error(f"[PID {pid}] Failed to access settings in worker: {e}", exc_info=True)

            # Проверяем, не инициализирован ли уже sync engine (на всякий случай)
            if db_manager.sync_engine is not None:
                logger.warning(f"[PID {pid}] Sync database already initialized, skipping")
            else:
                try:
                    # Инициализируем синхронный engine для Celery
                    db_manager.init_sync_engine(debug=settings.DEBUG)
                    logger.info(f"[PID {pid}] Sync database engine initialized successfully in Celery worker")
                except Exception as e:
                    logger.error(f"[PID {pid}] Failed to initialize sync database in Celery worker: {e}", exc_info=True)
                    # НЕ прерываем запуск воркера - некоторые задачи могут не требовать БД
                    # Воркер все равно должен быть способен выполнять задачи
                    logger.warning(f"[PID {pid}] Worker will continue, but database-dependent tasks may fail")

            # Инициализируем YooKassa SDK для Celery воркера
            try:
                if not settings.YOOKASSA_SHOP_ID or not settings.YOOKASSA_SECRET_KEY:
                    logger.warning(
                        f"[PID {pid}] YOOKASSA_SHOP_ID / YOOKASSA_SECRET_KEY not set, skipping YooKassa init"
                    )
                else:
                    yookassa_manager.configure()
                    logger.info(
                        f"[PID {pid}] YooKassa configuration initialized in Celery worker: "
                        f"account_id={str(settings.YOOKASSA_SHOP_ID)}"
                    )
            except Exception as e:
                logger.error(f"[PID {pid}] Failed to initialize YooKassa in Celery worker: {e}", exc_info=True)
                # НЕ прерываем запуск воркера - не все задачи требуют YooKassa
                logger.warning(f"[PID {pid}] Worker will continue, but YooKassa-dependent tasks may fail")

            # Проверяем, что задачи зарегистрированы
            try:
                registered_tasks = list(celery_app.tasks.keys())
                logger.info(
                    f"[PID {pid}] Registered Celery tasks ({len(registered_tasks)}): {', '.join(sorted(registered_tasks))}"
                )
            except Exception as e:
                logger.error(f"[PID {pid}] Failed to list registered tasks: {e}", exc_info=True)

            logger.info(f"[PID {pid}] Worker process initialization completed successfully")

        # Закрытие соединений при завершении worker процесса
        @worker_process_shutdown.connect
        def shutdown_worker_process(sender=None, **kwargs):
            """
            Закрыть все соединения с БД при завершении worker процесса.

            Это важно для правильной очистки ресурсов и предотвращения
            утечек соединений.
            """
            import os

            from app.core.database import db_manager
            from app.core.logger import logger

            pid = os.getpid()
            logger.info(f"[PID {pid}] worker_process_shutdown signal received")

            # Закрываем синхронный engine
            if db_manager.sync_engine is not None:
                try:
                    db_manager.sync_engine.dispose()
                    logger.info(f"[PID {pid}] Sync database connections closed")
                except Exception as e:
                    logger.warning(f"[PID {pid}] Error closing sync database connections: {e}")

    except Exception as e:
        # Redis not available or error during initialization, Celery will not be initialized
        logger.error(f"Failed to initialize Celery: {str(e)}", exc_info=True)
        celery_app = None
else:
    logger.warning(
        f"Celery not initialized: CELERY_BROKER_URL={settings.CELERY_BROKER_URL}, "
        f"CELERY_RESULT_BACKEND={settings.CELERY_RESULT_BACKEND}"
    )

# Алиас для совместимости с Celery CLI (ищет атрибут 'celery')
celery = celery_app
