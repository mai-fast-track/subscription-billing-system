"""
Payment-related Celery tasks
"""

from typing import Any

from app.celery_app import celery_app
from app.core.logger import logger
from app.tasks.utils import run_async


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
    name="app.tasks.payment.create_refund_for_card_change",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 минут между попытками
    acks_late=True,
)
def create_refund_for_card_change(self, payment_id: int) -> dict[str, Any]:
    """
    Создать возврат для платежа на смену карты.

    Эта задача запускается после успешной смены карты (обновления saved_payment_method_id).
    Создает возврат на сумму 1 рубль, которая была списана для привязки новой карты.

    Логика:
    1. Получить платеж по ID
    2. Проверить, что платеж успешен и имеет тип card_change
    3. Проверить, что возврат еще не создан
    4. Создать возврат через PaymentService.create_refund()
    5. Обработать ошибки с retry

    Args:
        payment_id: ID платежа для возврата

    Returns:
        Dict с результатом операции

    Raises:
        Exception: При ошибках, которые требуют retry
    """

    async def _create_refund():
        from app.core.clients.yookassa_client import yookassa_client
        from app.core.database import db_manager
        from app.database.unit_of_work import UnitOfWork
        from app.services.payment_service import PaymentService

        session = await db_manager.get_session()
        try:
            uow = UnitOfWork(session, yookassa_client)
            async with uow:
                payment_service = PaymentService(uow)

                # Получаем платеж
                payment = await uow.payments.get_by_id(payment_id)
                if not payment:
                    error_msg = f"Payment {payment_id} not found"
                    logger.error(error_msg)
                    return {"success": False, "error": error_msg}

                # Проверяем, что платеж успешен
                if payment.status != "succeeded":
                    error_msg = (
                        f"Payment {payment_id} is not succeeded (status: {payment.status}), cannot create refund"
                    )
                    logger.warning(error_msg)
                    return {"success": False, "error": error_msg}

                # Проверяем, что это платеж для смены карты
                if payment.payment_method != "card_change":
                    error_msg = f"Payment {payment_id} is not a card_change payment (method: {payment.payment_method})"
                    logger.warning(error_msg)
                    return {"success": False, "error": error_msg}

                # Проверяем, что возврат еще не создан
                existing_refund = await uow.refunds.get_by_payment_id(payment_id)
                if existing_refund:
                    logger.info(
                        f"Refund already exists for payment {payment_id} (refund_id={existing_refund.id}), skipping"
                    )
                    return {
                        "success": True,
                        "message": "Refund already exists",
                        "refund_id": existing_refund.id,
                    }

                # Создаем возврат на полную сумму платежа (1 рубль)
                reason = "Автоматический возврат средств после успешной смены карты для автосписаний"
                refund = await payment_service.create_refund(
                    payment_id=payment_id, amount=payment.amount, reason=reason
                )

                logger.info(
                    f"Successfully created refund {refund.id} for card change payment {payment_id}, "
                    f"amount={payment.amount} RUB"
                )

                return {
                    "success": True,
                    "message": "Refund created successfully",
                    "refund_id": refund.id,
                    "amount": payment.amount,
                }
        except ValueError as e:
            # ValueError означает, что возврат уже создан или платеж не подходит для возврата
            # Не ретраим такие ошибки
            error_msg = f"ValueError creating refund for payment {payment_id}: {str(e)}"
            logger.warning(error_msg)
            return {"success": False, "error": error_msg, "retry": False}
        except Exception as e:
            # Другие ошибки (например, YooKassa API недоступен) - ретраим
            error_msg = f"Error creating refund for payment {payment_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise  # Пробрасываем для retry
        finally:
            await session.close()

    try:
        result = run_async(_create_refund())
        return result
    except Exception as e:
        # Если это последняя попытка или ошибка не требует retry
        if self.request.retries >= self.max_retries:
            logger.error(f"Failed to create refund for payment {payment_id} after {self.max_retries} retries: {str(e)}")
            return {"success": False, "error": str(e), "retries_exceeded": True}

        # Пробрасываем для retry
        logger.warning(
            f"Retrying refund creation for payment {payment_id}, attempt {self.request.retries + 1}/{self.max_retries}"
        )
        raise self.retry(exc=e, countdown=self.default_retry_delay)


@celery_app.task(name="app.tasks.payment.retry_failed_payments")
def retry_failed_payments():
    """
    Retry failed payments that haven't exceeded max retries
    """
    # TODO: Implement retry failed payments logic
    # 1. Query failed payments with retry_count < max_retries
    # 2. Retry each payment
    # 3. Log results
    pass


@celery_app.task(name="app.tasks.payment.process_payment_async")
def process_payment_async(payment_id: int):
    """
    Process payment asynchronously
    """
    # TODO: Implement async payment processing
    # 1. Get payment from database
    # 2. Process payment
    # 3. Update status
    # 4. Send notifications
    pass
