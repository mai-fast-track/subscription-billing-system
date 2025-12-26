"""
Payment service - бизнес-логика для работы с платежами
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.enums import PaymentStatus, SubscriptionStatus
from app.core.logger import logger
from app.models import Payment, Refund
from app.schemas.payment import PaymentCreateRequest, PaymentCreateResponse
from app.schemas.refund import RefundResponse
from app.schemas.yookassa import YookassaPaymentRequest
from app.services.base_service import BaseService


class PaymentService(BaseService):
    """Сервис обработки платежей"""

    async def create_payment(self, payment_request: PaymentCreateRequest) -> PaymentCreateResponse:
        """
        Создать одностадийный платеж через Юкассу (старый метод).
        Платеж сразу списывается после подтверждения.
        """
        """
        Создать платеж через Юкассу
        
        Args:
            payment_request: Данные для создания платежа
            
        Returns:
            PaymentCreateResponse: Ответ с данными платежа
        """
        # Проверяем, что пользователь и подписка существуют
        await self.uow.users.get_by_id_or_raise(payment_request.user_id)
        await self.uow.subscriptions.get_by_id_or_raise(payment_request.subscription_id)

        idempotency_key = str(uuid.uuid4())

        # Создаем платеж в Юкассе
        description_extended = f"Подписка {payment_request.subscription_id} для пользователя {payment_request.user_id}"
        create_payment_request = YookassaPaymentRequest(
            amount_value=str(payment_request.amount),
            description=description_extended,
            return_url=payment_request.return_url,
        )

        yookassa_payment = self.uow.yookassa_client.create_payment(
            request=create_payment_request, idempotency_key=idempotency_key
        )

        # Создаем платеж в БД с ID от Юкассы
        from app.models import Payment

        db_payment = Payment(
            user_id=payment_request.user_id,
            subscription_id=payment_request.subscription_id,
            yookassa_payment_id=yookassa_payment.id,
            amount=payment_request.amount,
            currency="RUB",
            status="pending",
            attempt_number=1,
            idempotency_key=idempotency_key,
        )
        await self.uow.payments.create(db_payment)

        return PaymentCreateResponse(
            success=True,
            message="Платеж создан, переходите на оплату",
            confirmation_url=yookassa_payment.confirmation.confirmation_url,
            yookassa_payment_id=yookassa_payment.id,
        )

    async def create_payment_two_stage(self, payment_request: PaymentCreateRequest) -> PaymentCreateResponse:
        """
        Создать двухстадийный платеж через Юкассу (новый метод).
        Платеж сначала авторизуется, затем нужно вызвать capture_payment для списания.

        Args:
            payment_request: Данные для создания платежа

        Returns:
            PaymentCreateResponse: Ответ с данными платежа
        """
        # Проверяем, что пользователь и подписка существуют
        await self.uow.users.get_by_id_or_raise(payment_request.user_id)
        await self.uow.subscriptions.get_by_id_or_raise(payment_request.subscription_id)

        idempotency_key = str(uuid.uuid4())

        # Создаем двухстадийный платеж в Юкассе
        description_extended = f"Подписка {payment_request.subscription_id} для пользователя {payment_request.user_id}"
        create_payment_request = YookassaPaymentRequest(
            amount_value=str(payment_request.amount),
            description=description_extended,
            return_url=payment_request.return_url,
        )

        yookassa_payment = self.uow.yookassa_client.create_payment_two_stage(
            request=create_payment_request, idempotency_key=idempotency_key
        )

        # Создаем платеж в БД с ID от Юкассы
        db_payment = Payment(
            user_id=payment_request.user_id,
            subscription_id=payment_request.subscription_id,
            yookassa_payment_id=yookassa_payment.id,
            amount=payment_request.amount,
            currency="RUB",
            status=PaymentStatus.waiting_for_capture.value,
            attempt_number=1,
            idempotency_key=idempotency_key,
        )
        await self.uow.payments.create(db_payment)

        return PaymentCreateResponse(
            success=True,
            message="Платеж создан, переходите на оплату",
            confirmation_url=yookassa_payment.confirmation.confirmation_url,
            yookassa_payment_id=yookassa_payment.id,
        )

    async def capture_payment(self, payment_id: int) -> dict[str, Any]:
        """
        Провести (capture) двухстадийный платеж.
        Списывает ранее авторизованные средства.

        Args:
            payment_id: ID платежа в нашей БД

        Returns:
            Dict с результатом операции
        """
        # Получаем платеж из БД
        db_payment = await self.uow.payments.get_by_id_or_raise(payment_id)

        # Проверяем статус платежа
        if db_payment.status != PaymentStatus.waiting_for_capture.value:
            raise ValueError(
                f"Платеж {payment_id} не находится в статусе waiting_for_capture. Текущий статус: {db_payment.status}"
            )

        # Проводим платеж в Юкассе
        idempotency_key = str(uuid.uuid4())
        yookassa_payment = self.uow.yookassa_client.capture_payment(
            payment_id=db_payment.yookassa_payment_id, idempotency_key=idempotency_key
        )

        # Обновляем статус платежа в БД
        if yookassa_payment.status == "succeeded":
            db_payment.status = PaymentStatus.succeeded.value
            await self.uow.payments.update(db_payment)

            # Для платежей типа card_change не активируем подписку
            if db_payment.payment_method != "card_change":
                # Активируем подписку
                subscription = await self.uow.subscriptions.get_by_id_or_raise(db_payment.subscription_id)
                old_subscription_status = subscription.status
                subscription.status = SubscriptionStatus.active.value
                subscription.start_date = datetime.now(timezone.utc)
                await self.uow.subscriptions.update(subscription)

                # Явно делаем flush, чтобы изменения были сохранены в БД
                await self.uow.session.flush()

                # Обновляем объект из БД для получения актуальных данных
                await self.uow.session.refresh(subscription)

                from app.core.logger import logger

                logger.info(
                    f"Subscription {subscription.id} activated in capture_payment "
                    f"(status changed from {old_subscription_status} to {subscription.status})"
                )

            # Сохраняем платежный метод для будущих автоплатежей
            # ВАЖНО: Сохраняем только если пользователь явно дал согласие (payment_method.saved = true)
            try:
                from app.core.logger import logger
                from app.services.auto_payment_service import AutoPaymentService

                # Проверяем согласие пользователя из ответа capture_payment
                payment_method = None
                payment_method_saved = False
                payment_method_id = None

                # Извлекаем payment_method из ответа
                if hasattr(yookassa_payment, "payment_method") and yookassa_payment.payment_method:
                    payment_method = yookassa_payment.payment_method
                elif isinstance(yookassa_payment, dict) and yookassa_payment.get("payment_method"):
                    payment_method = yookassa_payment.get("payment_method")

                if payment_method:
                    # Извлекаем saved флаг
                    if hasattr(payment_method, "saved"):
                        payment_method_saved = bool(payment_method.saved)
                    elif isinstance(payment_method, dict):
                        payment_method_saved = bool(payment_method.get("saved", False))

                    # Извлекаем payment_method.id
                    if hasattr(payment_method, "id"):
                        payment_method_id = payment_method.id
                    elif isinstance(payment_method, dict):
                        payment_method_id = payment_method.get("id")

                # Сохраняем только если пользователь дал согласие (saved=True) и есть ID метода
                if payment_method_saved and payment_method_id:
                    # Проверяем, является ли это платежом для смены карты
                    if db_payment.payment_method == "card_change":
                        # Это платеж для смены карты - обновляем saved_payment_method_id
                        await self.uow.users.update_saved_payment_method(db_payment.user_id, payment_method_id)
                        logger.info(
                            f"Updated payment method for user {db_payment.user_id} "
                            f"from card change payment (capture): {payment_method_id}"
                        )
                    else:
                        # Обычный платеж - сохраняем через AutoPaymentService
                        auto_payment_service = AutoPaymentService(self.uow)
                        await auto_payment_service.save_payment_method_from_webhook(
                            db_payment.user_id, payment_method_id
                        )
                        logger.info(
                            f"Saved payment method ID for user {db_payment.user_id} from capture_payment: {payment_method_id} "
                            f"(user consented to auto payments)"
                        )
                elif not payment_method_saved:
                    logger.info(
                        f"Payment {db_payment.yookassa_payment_id} succeeded but user did not consent to save payment method "
                        f"(saved=False or missing). Payment method will not be saved for user {db_payment.user_id}"
                    )
                else:
                    # Если нет данных в capture_payment, делаем fallback запрос к API
                    logger.warning(
                        f"Payment {db_payment.yookassa_payment_id} capture response missing payment_method data, "
                        f"falling back to API request"
                    )
                    auto_payment_service = AutoPaymentService(self.uow)
                    await auto_payment_service.save_payment_method_after_success(
                        db_payment.user_id, db_payment.yookassa_payment_id
                    )
            except Exception as e:
                # Логируем ошибку, но не прерываем обработку
                from app.core.logger import logger

                logger.error(f"Error saving payment method: {str(e)}")

            # Формируем сообщение в зависимости от типа платежа
            if db_payment.payment_method == "card_change":
                message = "Платеж успешно проведен, карта обновлена для автосписаний"
            else:
                message = "Платеж успешно проведен, подписка активирована"

            return {
                "success": True,
                "message": message,
                "payment_id": payment_id,
                "yookassa_payment_id": db_payment.yookassa_payment_id,
            }
        else:
            # Обновляем статус на основе ответа от Юкассы
            db_payment.status = yookassa_payment.status
            await self.uow.payments.update(db_payment)

            return {
                "success": False,
                "message": f"Платеж не проведен. Статус: {yookassa_payment.status}",
                "payment_id": payment_id,
            }

    async def cancel_payment(self, payment_id: int) -> dict[str, Any]:
        """
        Отменить платеж в Юкассе и обновить статус в БД.
        Поддерживает отмену платежей в статусах pending и waiting_for_capture.

        Args:
            payment_id: ID платежа в нашей БД

        Returns:
            Dict с результатом операции
        """
        # Получаем платеж из БД
        db_payment = await self.uow.payments.get_by_id_or_raise(payment_id)

        # Проверяем, можно ли отменить платеж
        if db_payment.status not in [PaymentStatus.waiting_for_capture.value, PaymentStatus.pending.value]:
            raise ValueError(f"Платеж {payment_id} нельзя отменить. Текущий статус: {db_payment.status}")

        # Отменяем платеж в Юкассе
        idempotency_key = str(uuid.uuid4())
        self.uow.yookassa_client.cancel_payment(
            payment_id=db_payment.yookassa_payment_id, idempotency_key=idempotency_key
        )

        # Обновляем статус платежа в БД
        db_payment.status = PaymentStatus.cancelled.value
        await self.uow.payments.update(db_payment)

        return {
            "success": True,
            "message": "Платеж успешно отменен",
            "payment_id": payment_id,
            "yookassa_payment_id": db_payment.yookassa_payment_id,
        }

    async def process_webhook(self, webhook_data: dict[str, Any]) -> dict[str, str]:
        """
        Обработать webhook от Юкассы о статусе платежа или возврата.
        Обрабатывает одностадийные платежи и возвраты.

        Args:
            webhook_data: Данные webhook от Юкассы

        Returns:
            Dict с результатом обработки
        """
        from app.core.logger import logger

        # Логируем входящий webhook для отладки
        event = webhook_data.get("event")
        logger.info(f"Processing webhook: event={event}, data={webhook_data}")

        # Обработка webhook для возвратов
        if event == "refund.succeeded":
            return await self._process_refund_webhook(webhook_data)

        # Обработка webhook для платежей (существующая логика)
        webhook_object = webhook_data.get("object", {})
        yookassa_payment_id = webhook_object.get("id")
        payment_status = webhook_object.get("status")

        if not yookassa_payment_id:
            logger.warning("Webhook received without payment ID")
            return {"status": "ok", "message": "No payment ID in webhook"}

        # Получаем платеж из БД
        db_payment = await self.uow.payments.get_payment_by_yookassa_id(yookassa_payment_id)

        if not db_payment:
            logger.warning(f"Payment not found in DB for yookassa_payment_id: {yookassa_payment_id}")
            # Тихо игнорируем, Юкассе не важно
            return {"status": "ok", "message": "Payment not found"}

        # Обновляем статус платежа в БД на основе статуса от Юкассы
        old_payment_status = db_payment.status
        if payment_status != db_payment.status:
            if payment_status == "succeeded":
                db_payment.status = PaymentStatus.succeeded.value
            elif payment_status == "canceled":
                db_payment.status = PaymentStatus.cancelled.value
            elif payment_status == "pending":
                db_payment.status = PaymentStatus.pending.value
            else:
                db_payment.status = payment_status

            await self.uow.payments.update(db_payment)
            logger.info(f"Updated payment {db_payment.id} status from {old_payment_status} to {db_payment.status}")

        # Обработка для успешных платежей
        if payment_status == "succeeded":
            # Получаем подписку
            subscription = await self.uow.subscriptions.get_by_id_or_raise(db_payment.subscription_id)

            # Проверяем, является ли это автоплатежем
            is_auto_payment = db_payment.payment_method == "auto_payment"

            if is_auto_payment:
                # Для автоплатежей - продлеваем подписку с идемпотентностью
                try:
                    from app.services.auto_payment_service import AutoPaymentService

                    auto_payment_service = AutoPaymentService(self.uow)

                    # 🔍 ИДЕМПОТЕНТНОСТЬ: Проверяем, не была ли подписка уже продлена
                    # (защита от двойного продления, если webhook приходит после retry_auto_payment_attempt)
                    if await auto_payment_service._is_subscription_already_extended(subscription.id):
                        logger.info(
                            f"Subscription {subscription.id} already extended (possibly by retry_auto_payment_attempt), "
                            f"skipping webhook renewal"
                        )
                    else:
                        # Получаем план для определения длительности
                        plan = await self.uow.subscription_plans.get_by_id_or_raise(subscription.plan_id)

                        # Продлеваем подписку с обновлением дат
                        await auto_payment_service._renew_subscription(subscription, plan.duration_days)

                        # Обновляем объект subscription из БД для получения актуальных дат
                        subscription = await self.uow.subscriptions.get_by_id_or_raise(db_payment.subscription_id)

                        # Отправляем уведомление
                        await auto_payment_service._send_notification(
                            subscription.user_id,
                            f"Автоплатеж успешно проведен. Подписка продлена до {subscription.end_date.strftime('%d.%m.%Y')}",
                        )
                except Exception as e:
                    logger.error(f"Error processing auto payment renewal: {str(e)}")
            else:
                # Для платежей типа card_change не активируем подписку
                if db_payment.payment_method == "card_change":
                    logger.info(f"Payment {db_payment.id} is card_change type, skipping subscription activation")
                # Для обычных платежей - активируем подписку из pending_payment в active
                elif subscription.status == SubscriptionStatus.pending_payment.value:
                    old_subscription_status = subscription.status
                    subscription.status = SubscriptionStatus.active.value
                    subscription.start_date = datetime.now(timezone.utc)
                    await self.uow.subscriptions.update(subscription)

                    # Обновляем объект из БД для получения актуальных данных
                    await self.uow.session.refresh(subscription)

                    logger.info(
                        f"Subscription {subscription.id} activated after payment {db_payment.id} succeeded "
                        f"(status changed from {old_subscription_status} to {subscription.status})"
                    )
                elif (
                    subscription.status
                    in [
                        SubscriptionStatus.cancelled.value,
                        SubscriptionStatus.cancelled_waiting.value,
                    ]
                    and db_payment.payment_method != "card_change"
                ):
                    # Пользователь оплатил после того, как подписка была отменена (нет saved_payment_method_id)
                    # Активируем подписку и продлеваем её
                    # Для платежей типа card_change не активируем подписку
                    try:
                        from app.services.auto_payment_service import AutoPaymentService

                        auto_payment_service = AutoPaymentService(self.uow)

                        # Получаем план для определения длительности
                        plan = await self.uow.subscription_plans.get_by_id_or_raise(subscription.plan_id)

                        # Активируем и продлеваем подписку
                        subscription.status = SubscriptionStatus.active.value
                        subscription.start_date = datetime.now(timezone.utc)
                        await auto_payment_service._renew_subscription(subscription, plan.duration_days)

                        # Обновляем объект из БД для получения актуальных данных
                        await self.uow.session.refresh(subscription)

                        logger.info(
                            f"Subscription {subscription.id} reactivated and extended after payment {db_payment.id} succeeded "
                            f"(status changed from {old_subscription_status} to {subscription.status}, "
                            f"end_date={subscription.end_date})"
                        )

                        # Отправляем уведомление
                        await auto_payment_service._send_notification(
                            subscription.user_id,
                            f"Платеж успешно проведен. Подписка активирована и продлена до {subscription.end_date.strftime('%d.%m.%Y')}",
                        )
                    except Exception as e:
                        logger.error(f"Error reactivating cancelled subscription {subscription.id}: {str(e)}")
                elif subscription.status != SubscriptionStatus.active.value:
                    # Если подписка не в pending_payment, не cancelled, и не активна, логируем
                    logger.warning(
                        f"Payment {db_payment.id} succeeded, but subscription {subscription.id} "
                        f"is in status {subscription.status}, not activating"
                    )

            # Сохраняем платежный метод для будущих автоплатежей
            # ВАЖНО: Сохраняем только если пользователь явно дал согласие (payment_method.saved = true)
            try:
                # Извлекаем информацию о платежном методе из вебхука
                payment_method_data = webhook_object.get("payment_method", {})
                payment_method_saved = payment_method_data.get("saved", False)
                payment_method_id = payment_method_data.get("id")

                # Сохраняем только если пользователь разрешил автосписания (saved=True) и есть ID метода
                if payment_method_saved and payment_method_id:
                    # Проверяем, является ли это платежом для смены карты
                    if db_payment.payment_method == "card_change":
                        # Это платеж для смены карты - обновляем saved_payment_method_id
                        try:
                            await self.uow.users.update_saved_payment_method(db_payment.user_id, payment_method_id)
                            logger.info(
                                f"Updated payment method for user {db_payment.user_id} "
                                f"from card change webhook: {payment_method_id}"
                            )

                            # После успешного обновления карты запускаем задачу для возврата средств
                            try:
                                from app.celery_app import celery_app

                                if celery_app is not None:
                                    from app.tasks.payment import create_refund_for_card_change

                                    # Запускаем задачу асинхронно
                                    create_refund_for_card_change.delay(db_payment.id)
                                    logger.info(
                                        f"Scheduled refund task for card change payment {db_payment.id} "
                                        f"(user {db_payment.user_id})"
                                    )
                                else:
                                    logger.warning(
                                        f"Celery not initialized, cannot schedule refund for payment {db_payment.id}. "
                                        f"Refund will need to be created manually."
                                    )
                            except Exception as refund_task_error:
                                # Логируем ошибку, но не прерываем обработку webhook
                                logger.error(
                                    f"Failed to schedule refund task for payment {db_payment.id}: {str(refund_task_error)}",
                                    exc_info=True,
                                )
                        except Exception as update_error:
                            # Если не удалось обновить payment_method_id, не запускаем возврат
                            logger.error(
                                f"Failed to update payment method for user {db_payment.user_id} "
                                f"from card change payment {db_payment.id}: {str(update_error)}",
                                exc_info=True,
                            )
                            # Пробрасываем ошибку, чтобы она была видна в логах
                            raise
                    else:
                        # Обычный платеж - сохраняем через AutoPaymentService
                        from app.services.auto_payment_service import AutoPaymentService

                        auto_payment_service = AutoPaymentService(self.uow)
                        await auto_payment_service.save_payment_method_from_webhook(
                            db_payment.user_id, payment_method_id
                        )
                        logger.info(
                            f"Saved payment method ID for user {db_payment.user_id} from webhook: {payment_method_id} "
                            f"(user consented to auto payments)"
                        )
                elif payment_method_saved and not payment_method_id:
                    # Если saved=True, но нет ID - делаем запрос к API как fallback
                    logger.warning(
                        f"Payment {yookassa_payment_id} has saved=True but no payment_method.id in webhook, "
                        f"falling back to API request"
                    )
                    from app.services.auto_payment_service import AutoPaymentService

                    auto_payment_service = AutoPaymentService(self.uow)
                    await auto_payment_service.save_payment_method_after_success(
                        db_payment.user_id, yookassa_payment_id
                    )
                elif not payment_method_saved:
                    logger.info(
                        f"Payment {yookassa_payment_id} succeeded but user did not consent to save payment method "
                        f"(saved=False or missing). Payment method will not be saved for user {db_payment.user_id}"
                    )
            except Exception as e:
                # Логируем ошибку, но не прерываем обработку
                logger.error(f"Error saving payment method: {str(e)}")

            return {
                "status": "ok",
                "message": "Payment succeeded, subscription activated"
                if not is_auto_payment
                else "Auto payment succeeded, subscription renewed",
            }

        # Обработка отмененных платежей
        if payment_status == "canceled":
            logger.info(f"Payment {db_payment.id} cancelled via webhook")
            return {"status": "ok", "message": "Payment cancelled"}

        # Все остальные статусы
        logger.info(f"Webhook processed for payment {db_payment.id} with status: {payment_status}")
        return {"status": "ok", "message": f"Webhook processed. Status: {payment_status}"}

    async def create_payment_for_card_change(
        self, user_id: int, return_url: str, amount: float = 1.0
    ) -> PaymentCreateResponse:
        """
        Создать платеж для смены карты, используемой для автосписаний.

        Создает одностадийный платеж с минимальной суммой для привязки новой карты.
        После успешного платежа payment_method_id будет автоматически обновлен через webhook.

        Args:
            user_id: ID пользователя
            return_url: URL для возврата после оплаты
            amount: Минимальная сумма для привязки карты (по умолчанию 1 рубль)

        Returns:
            PaymentCreateResponse: Ответ с данными платежа
        """
        from app.core.logger import logger

        # Проверяем, что пользователь существует
        await self.uow.users.get_by_id_or_raise(user_id)

        # Получаем активную подписку пользователя (если есть)
        active_subscription = await self.uow.subscriptions.get_active_subscription(user_id)

        if not active_subscription:
            # Если нет активной подписки, получаем любую существующую подписку пользователя
            all_subscriptions = await self.uow.subscriptions.get_all_user_subscriptions(user_id)
            if all_subscriptions:
                subscription_id = all_subscriptions[0].id
                logger.info(f"Using existing subscription {subscription_id} for card change payment (user {user_id})")
            else:
                # Если нет подписок, нельзя создать платеж для смены карты
                raise ValueError("У пользователя нет подписки. Для смены карты необходима хотя бы одна подписка.")
        else:
            subscription_id = active_subscription.id
            logger.info(f"Using active subscription {subscription_id} for card change payment (user {user_id})")

        idempotency_key = f"change_card_{user_id}_{uuid.uuid4()}"

        # Создаем одностадийный платеж в Юкассе для привязки новой карты
        description = f"Привязка новой карты для автосписаний (пользователь {user_id})"
        create_payment_request = YookassaPaymentRequest(
            amount_value=str(amount),
            description=description,
            return_url=return_url,
        )

        yookassa_payment = self.uow.yookassa_client.create_payment(
            request=create_payment_request, idempotency_key=idempotency_key
        )

        # Создаем платеж в БД с ID от Юкассы
        db_payment = Payment(
            user_id=user_id,
            subscription_id=subscription_id,
            yookassa_payment_id=yookassa_payment.id,
            amount=amount,
            currency="RUB",
            status=PaymentStatus.pending.value,
            attempt_number=1,
            idempotency_key=idempotency_key,
            payment_method="card_change",  # Специальный тип для смены карты
        )
        await self.uow.payments.create(db_payment)

        logger.info(
            f"Created payment {db_payment.id} for card change (user {user_id}, "
            f"yookassa_payment_id={yookassa_payment.id})"
        )

        return PaymentCreateResponse(
            success=True,
            message="Платеж создан для привязки новой карты. После успешной оплаты карта будет обновлена.",
            confirmation_url=yookassa_payment.confirmation.confirmation_url,
            yookassa_payment_id=yookassa_payment.id,
        )

    async def get_user_completed_payments(self, user_id: int, skip: int = 0, limit: int = 100) -> list[Payment]:
        """
        Получить платежи пользователя в конечных статусах (succeeded, cancelled, failed)

        Args:
            user_id: ID пользователя
            skip: Количество пропущенных записей
            limit: Максимальное количество записей

        Returns:
            Список платежей в конечных статусах, отсортированных по дате создания (новые сначала)
        """
        # Проверяем, что пользователь существует
        await self.uow.users.get_by_id_or_raise(user_id)

        # Получаем платежи в конечных статусах через репозиторий
        payments = await self.uow.payments.get_user_completed_payments(user_id, skip=skip, limit=limit)

        return list(payments)

    async def _process_refund_webhook(self, webhook_data: dict[str, Any]) -> dict[str, str]:
        """
        Обработать webhook о возврате от Юкассы.

        Args:
            webhook_data: Данные webhook от Юкассы

        Returns:
            Dict с результатом обработки
        """
        webhook_object = webhook_data.get("object", {})
        yookassa_refund_id = webhook_object.get("id")
        refund_status = webhook_object.get("status")

        if not yookassa_refund_id:
            logger.warning("Refund webhook received without refund ID")
            return {"status": "ok", "message": "No refund ID in webhook"}

        # Получаем возврат из БД
        db_refund = await self.uow.refunds.get_by_yookassa_id(yookassa_refund_id)

        if not db_refund:
            logger.warning(f"Refund not found in DB for yookassa_refund_id: {yookassa_refund_id}")
            return {"status": "ok", "message": "Refund not found"}

        # Обновляем статус возврата в БД
        old_refund_status = db_refund.status
        if refund_status != db_refund.status:
            db_refund.status = refund_status
            await self.uow.refunds.update(db_refund)
            logger.info(
                f"Updated refund {db_refund.id} status from {old_refund_status} to {refund_status} "
                f"(yookassa_refund_id={yookassa_refund_id})"
            )

        return {"status": "ok", "message": "Refund webhook processed"}

    async def calculate_refund_amount(self, payment: Payment, subscription) -> float:
        """
        Вычислить сумму возврата по политике.

        Политика возврата:
        - Если платеж был менее 14 дней назад - полный возврат
        - Если больше 14 дней - частичный возврат (пропорционально неиспользованному периоду)
        - Триал-платежи (yookassa_payment_id == "trial_period") не возвращаются

        Args:
            payment: Платеж для возврата
            subscription: Подписка, связанная с платежом

        Returns:
            float: Сумма возврата (0.0 если возврат не положен)
        """
        # Триал-платежи не возвращаем
        if payment.yookassa_payment_id == "trial_period":
            logger.info(f"Payment {payment.id} is trial payment, refund not applicable")
            return 0.0

        now = datetime.now(timezone.utc)
        payment_date = payment.created_at

        # Вычисляем количество дней с момента платежа
        days_since_payment = (now - payment_date).days

        # Если платеж был менее 14 дней назад - полный возврат
        REFUND_FULL_PERIOD_DAYS = 14
        if days_since_payment <= REFUND_FULL_PERIOD_DAYS:
            logger.info(f"Payment {payment.id} was {days_since_payment} days ago, full refund: {payment.amount} RUB")
            return round(payment.amount, 2)

        # Если больше 14 дней - частичный возврат (пропорционально неиспользованному периоду)
        # Вычисляем сколько дней осталось до end_date
        days_remaining = (subscription.end_date - now).days
        if days_remaining <= 0:
            logger.info(f"Payment {payment.id} subscription period expired, no refund")
            return 0.0

        # Вычисляем общее количество дней подписки
        # Нужно получить план для определения длительности
        plan = await self.uow.subscription_plans.get_by_id_or_raise(subscription.plan_id)
        total_days = plan.duration_days

        if total_days <= 0:
            logger.warning(f"Plan {plan.id} has invalid duration_days: {total_days}, cannot calculate refund")
            return 0.0

        # Пропорциональный возврат
        refund_ratio = days_remaining / total_days
        refund_amount = round(payment.amount * refund_ratio, 2)

        logger.info(
            f"Payment {payment.id} was {days_since_payment} days ago, "
            f"partial refund: {refund_amount} RUB ({days_remaining}/{total_days} days remaining)"
        )

        return refund_amount

    async def create_refund(self, payment_id: int, amount: float, reason: str | None = None) -> RefundResponse:
        """
        Создать возврат через YooKassa.

        Args:
            payment_id: ID платежа для возврата
            amount: Сумма возврата
            reason: Причина возврата (опционально)

        Returns:
            RefundResponse: Информация о созданном возврате

        Raises:
            ValueError: Если платеж не найден, не успешен, или возврат уже создан
        """
        # Получаем платеж
        payment = await self.uow.payments.get_by_id_or_raise(payment_id)

        # Проверяем, что платеж успешен
        if payment.status != PaymentStatus.succeeded.value:
            raise ValueError(f"Нельзя вернуть платеж со статусом {payment.status}. Требуется статус 'succeeded'")

        # Проверяем, что не был уже возврат
        existing_refund = await self.uow.refunds.get_by_payment_id(payment_id)
        if existing_refund:
            raise ValueError(f"Возврат для платежа {payment_id} уже создан (refund_id={existing_refund.id})")

        # Проверяем сумму возврата
        if amount <= 0:
            raise ValueError(f"Сумма возврата должна быть больше 0, получено: {amount}")
        if amount > payment.amount:
            raise ValueError(f"Сумма возврата ({amount}) не может быть больше суммы платежа ({payment.amount})")

        # Создаем возврат через YooKassa
        idempotency_key = str(uuid.uuid4())
        try:
            refund_response = self.uow.yookassa_client.create_refund(
                payment_id=payment.yookassa_payment_id,
                amount=amount,
                idempotency_key=idempotency_key,
            )

            # Сохраняем возврат в БД
            refund = Refund(
                payment_id=payment_id,
                yookassa_refund_id=refund_response.id,
                amount=amount,
                currency=payment.currency,
                status=refund_response.status,
                reason=reason,
            )

            created_refund = await self.uow.refunds.create(refund)

            logger.info(
                f"Created refund {created_refund.id} for payment {payment_id}: "
                f"amount={amount} RUB, yookassa_refund_id={refund_response.id}, status={refund_response.status}"
            )

            return RefundResponse.model_validate(created_refund)

        except Exception as e:
            logger.error(f"Error creating refund for payment {payment_id}: {str(e)}")
            raise
