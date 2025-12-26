# ============================================
# FASTAPI ENDPOINTS ДЛЯ ПЛАТЕЖЕЙ
# ===========================================


from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.database import get_uow
from app.database.unit_of_work import UnitOfWork
from app.schemas.payment import (
    ChangePaymentMethodRequest,
    PaymentCreateRequest,
    PaymentCreateResponse,
    PaymentWithSubscriptionResponse,
)
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


# ============================================
# ENDPOINTS - ОДНОСТАДИЙНЫЕ ПЛАТЕЖИ (старый метод)
# ===========================================


@router.post("/create", response_model=PaymentCreateResponse)
async def create_payment(request: PaymentCreateRequest, uow: UnitOfWork = Depends(get_uow)):
    """
    Endpoint: Создание одностадийного платежа (старый метод)

    Платеж сразу списывается после подтверждения пользователем.

    POST /api/v1/payments/create
    {
        "user_id": 1,
        "subscription_id": 5,
        "amount": 99.00,
        "return_url": "https://yourdomain.com/subscription/success"
    }

    Response:
    {
        "success": true,
        "message": "Платеж создан, переходите на оплату",
        "confirmation_url": "https://yookassa.ru/payments/...",
        "yookassa_payment_id": "29f87ba5-000f-50df-a9f3-7a84e1cc9f45"
    }
    """
    async with uow:
        try:
            service = PaymentService(uow)
            result = await service.create_payment(request)
            return result
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except RuntimeError as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Внутренняя ошибка: {str(e)}"
            )


@router.post("/create-two-stage", response_model=PaymentCreateResponse)
async def create_payment_two_stage(request: PaymentCreateRequest, uow: UnitOfWork = Depends(get_uow)):
    """
    Endpoint: Создание двухстадийного платежа (новый метод)

    Платеж сначала авторизуется, затем нужно вызвать /capture для списания.
    Это позволяет отменить платеж до его проведения.

    POST /api/v1/payments/create-two-stage
    {
        "user_id": 1,
        "subscription_id": 5,
        "amount": 99.00,
        "return_url": "https://yourdomain.com/subscription/success"
    }

    Response:
    {
        "success": true,
        "message": "Платеж создан, переходите на оплату",
        "confirmation_url": "https://yookassa.ru/payments/...",
        "yookassa_payment_id": "29f87ba5-000f-50df-a9f3-7a84e1cc9f45"
    }
    """
    async with uow:
        try:
            service = PaymentService(uow)
            result = await service.create_payment_two_stage(request)
            return result
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except RuntimeError as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Внутренняя ошибка: {str(e)}"
            )


@router.post("/{payment_id}/capture")
async def capture_payment(payment_id: int, uow: UnitOfWork = Depends(get_uow)):
    """
    Endpoint: Провести (capture) двухстадийный платеж

    Списывает ранее авторизованные средства.

    POST /api/v1/payments/{payment_id}/capture

    Response:
    {
        "success": true,
        "message": "Платеж успешно проведен, подписка активирована",
        "payment_id": 1,
        "yookassa_payment_id": "29f87ba5-000f-50df-a9f3-7a84e1cc9f45"
    }
    """
    async with uow:
        try:
            service = PaymentService(uow)
            result = await service.capture_payment(payment_id)
            return result
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except RuntimeError as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Внутренняя ошибка: {str(e)}"
            )


@router.post("/{payment_id}/cancel")
async def cancel_payment(payment_id: int, uow: UnitOfWork = Depends(get_uow)):
    """
    Endpoint: Отменить платеж

    Отменяет авторизованные средства для двухстадийного платежа.
    Можно использовать для отмены платежа до его проведения.

    POST /api/v1/payments/{payment_id}/cancel

    Response:
    {
        "success": true,
        "message": "Платеж успешно отменен",
        "payment_id": 1,
        "yookassa_payment_id": "29f87ba5-000f-50df-a9f3-7a84e1cc9f45"
    }
    """
    async with uow:
        try:
            service = PaymentService(uow)
            result = await service.cancel_payment(payment_id)
            return result
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except RuntimeError as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Внутренняя ошибка: {str(e)}"
            )


@router.post("/change-payment-method", response_model=PaymentCreateResponse)
async def change_payment_method(request: ChangePaymentMethodRequest, uow: UnitOfWork = Depends(get_uow)):
    """
    Endpoint: Смена карты для автосписаний

    Создает платеж с минимальной суммой (по умолчанию 1 рубль) для привязки новой карты.
    После успешной оплаты новая карта будет использоваться для автосписаний.

    POST /api/v1/payments/change-payment-method
    {
        "user_id": 1,
        "return_url": "https://yourdomain.com/payment/success",
        "amount": 1.0
    }

    Response:
    {
        "success": true,
        "message": "Платеж создан для привязки новой карты. После успешной оплаты карта будет обновлена.",
        "confirmation_url": "https://yookassa.ru/payments/...",
        "yookassa_payment_id": "29f87ba5-000f-50df-a9f3-7a84e1cc9f45"
    }
    """
    async with uow:
        try:
            service = PaymentService(uow)
            result = await service.create_payment_for_card_change(
                user_id=request.user_id, return_url=request.return_url, amount=request.amount
            )
            return result
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except RuntimeError as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Внутренняя ошибка: {str(e)}"
            )


@router.post("/webhook")
async def yookassa_webhook(request: Request, uow: UnitOfWork = Depends(get_uow)):
    """
    Endpoint: Webhook от Юкассы

    Юкасса отправит POST запрос на этот URL с информацией о платеже.
    Обрабатывает одностадийные платежи.

    Нужно добавить в настройках Юкассы:
    https://yookassa.ru/my/merchant/integration/http-notifications

    URL для настройки в Юкассе:
    - Локально (для тестирования): http://localhost:8000/api/v1/payments/webhook
    - Продакшн: https://yourdomain.com/api/v1/payments/webhook

    Важно: Endpoint должен быть доступен из интернета для получения webhook от Юкассы.
    Для локальной разработки можно использовать ngrok или аналогичные сервисы.

    Примечание: Для ngrok используйте команду: ngrok http 8000
    """
    from app.core.logger import logger

    try:
        webhook_data = await request.json()

        logger.info(f"Webhook received: {webhook_data}")
        logger.info(f"Webhook headers: {dict(request.headers)}")

        async with uow:
            try:
                service = PaymentService(uow)
                result = await service.process_webhook(webhook_data)
                logger.info(f"Webhook processed successfully: {result}")
                return result
            except Exception as e:
                # Юкассе важно, чтобы мы вернули 200, даже если была ошибка
                logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
                return {"status": "ok", "message": "Webhook received"}
    except Exception as e:
        # Ошибка при парсинге JSON - логируем и возвращаем 200
        logger.error(f"Webhook JSON parsing error: {str(e)}", exc_info=True)
        return {"status": "ok", "message": "Webhook received"}


@router.get("/user/{user_id}", response_model=list[PaymentWithSubscriptionResponse])
async def get_user_payments(
    user_id: int,
    skip: int = Query(0, ge=0, description="Количество пропущенных записей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Endpoint: Получить все платежи пользователя с информацией о подписках

    GET /api/v1/payments/user/{user_id}?skip=0&limit=100

    Response:
    [
        {
            "id": 1,
            "user_id": 1,
            "subscription_id": 5,
            "yookassa_payment_id": "29f87ba5-000f-50df-a9f3-7a84e1cc9f45",
            "amount": 99.00,
            "currency": "RUB",
            "status": "succeeded",
            "payment_method": "manual",
            "attempt_number": 1,
            "created_at": "2025-01-27T12:00:00Z",
            "updated_at": "2025-01-27T12:00:00Z",
            "subscription_plan_name": "Premium",
            "subscription_status": "active"
        }
    ]
    """
    async with uow:
        try:
            payments = await uow.payments.get_user_payments(user_id)

            # Сортируем по дате создания (новые сначала)
            payments = sorted(payments, key=lambda p: p.created_at, reverse=True)

            payments = payments[skip : skip + limit]

            # Формируем ответ с информацией о подписках и возвратах
            result = []
            for payment in payments:
                subscription_plan_name = None
                subscription_status = None
                refund_amount = None
                refund_status = None

                try:
                    if payment.subscription_id:
                        subscription = await uow.subscriptions.get_by_id(payment.subscription_id)

                        if subscription:
                            subscription_status = subscription.status
                            try:
                                if subscription.plan_id:
                                    plan = await uow.subscription_plans.get_by_id(subscription.plan_id)
                                    if plan:
                                        subscription_plan_name = plan.name
                            except Exception as plan_error:
                                from app.core.logger import logger

                                logger.warning(
                                    f"Error getting plan {subscription.plan_id} for subscription {subscription.id}: {plan_error}"
                                )
                except Exception as sub_error:
                    from app.core.logger import logger

                    logger.warning(
                        f"Error getting subscription {payment.subscription_id} for payment {payment.id}: {sub_error}"
                    )

                try:
                    refund = await uow.refunds.get_by_payment_id(payment.id)
                    if refund:
                        refund_amount = refund.amount
                        refund_status = refund.status
                except Exception as refund_error:
                    from app.core.logger import logger

                    logger.warning(f"Error getting refund for payment {payment.id}: {refund_error}")

                result.append(
                    PaymentWithSubscriptionResponse(
                        id=payment.id,
                        user_id=payment.user_id,
                        subscription_id=payment.subscription_id,
                        yookassa_payment_id=payment.yookassa_payment_id,
                        amount=payment.amount,
                        currency=payment.currency,
                        status=payment.status,
                        payment_method=payment.payment_method,
                        attempt_number=payment.attempt_number,
                        created_at=payment.created_at,
                        updated_at=payment.updated_at,
                        subscription_plan_name=subscription_plan_name,
                        subscription_status=subscription_status,
                        refund_amount=refund_amount,
                        refund_status=refund_status,
                    )
                )

            return result
        except Exception as e:
            from app.core.logger import logger

            logger.error(f"Error getting user payments: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Внутренняя ошибка: {str(e)}"
            )


@router.get("/user/{user_id}/completed", response_model=list[PaymentWithSubscriptionResponse])
async def get_user_completed_payments(
    user_id: int,
    skip: int = Query(0, ge=0, description="Количество пропущенных записей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Endpoint: Получить платежи пользователя в конечных статусах (succeeded, cancelled, failed)

    Возвращает только завершенные платежи (успешные, отмененные или неудачные).
    Не включает pending и waiting_for_capture платежи.

    GET /api/v1/payments/user/{user_id}/completed?skip=0&limit=100

    Response:
    [
        {
            "id": 1,
            "user_id": 1,
            "subscription_id": 5,
            "yookassa_payment_id": "29f87ba5-000f-50df-a9f3-7a84e1cc9f45",
            "amount": 99.00,
            "currency": "RUB",
            "status": "succeeded",
            "payment_method": "manual",
            "attempt_number": 1,
            "created_at": "2025-01-27T12:00:00Z",
            "updated_at": "2025-01-27T12:00:00Z",
            "subscription_plan_name": "Premium",
            "subscription_status": "active"
        }
    ]
    """
    from app.core.logger import logger

    async with uow:
        try:
            service = PaymentService(uow)
            payments = await service.get_user_completed_payments(user_id, skip=skip, limit=limit)

            result = []
            for payment in payments:
                subscription_plan_name = None
                subscription_status = None

                try:
                    if payment.subscription_id:
                        subscription = await uow.subscriptions.get_by_id(payment.subscription_id)

                        if subscription:
                            subscription_status = subscription.status
                            try:
                                if subscription.plan_id:
                                    plan = await uow.subscription_plans.get_by_id(subscription.plan_id)
                                    if plan:
                                        subscription_plan_name = plan.name
                            except Exception as plan_error:
                                logger.warning(
                                    f"Error getting plan {subscription.plan_id} for subscription {subscription.id}: {plan_error}"
                                )
                except Exception as sub_error:
                    logger.warning(
                        f"Error getting subscription {payment.subscription_id} for payment {payment.id}: {sub_error}"
                    )

                result.append(
                    PaymentWithSubscriptionResponse(
                        id=payment.id,
                        user_id=payment.user_id,
                        subscription_id=payment.subscription_id,
                        yookassa_payment_id=payment.yookassa_payment_id,
                        amount=payment.amount,
                        currency=payment.currency,
                        status=payment.status,
                        payment_method=payment.payment_method,
                        attempt_number=payment.attempt_number,
                        created_at=payment.created_at,
                        updated_at=payment.updated_at,
                        subscription_plan_name=subscription_plan_name,
                        subscription_status=subscription_status,
                    )
                )

            return result
        except Exception as e:
            logger.error(f"Error getting user completed payments: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Внутренняя ошибка: {str(e)}"
            )
