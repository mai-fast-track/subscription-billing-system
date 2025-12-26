"""
Auto Payment Service - сервис для автоматических платежей подписок
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.enums import PaymentStatus, SubscriptionStatus
from app.core.logger import logger
from app.models import Payment, Subscription
from app.schemas.subscription import SubscriptionWithPaymentRequest
from app.services.base_service import BaseService
from app.services.subscription_orchestrator_service import SubscriptionOrchestratorService


class AutoPaymentService(BaseService):
    """Сервис для обработки автоматических платежей подписок"""

    MAX_RETRY_ATTEMPTS = 3
    RETRY_DELAY_SECONDS = 300  # 5 минут

    async def process_auto_payments_for_today(self) -> dict[str, Any]:
        """
        Обработать автоплатежи для всех подписок, которые заканчиваются сегодня

        Returns:
            Dict с результатами обработки
        """
        subscriptions = await self.uow.subscriptions.get_subscriptions_ending_today()

        results = {"total": len(subscriptions), "success": 0, "failed": 0, "no_payment_method": 0, "errors": []}

        for subscription in subscriptions:
            try:
                result = await self._process_single_auto_payment(subscription)
                if result["success"]:
                    results["success"] += 1
                elif result.get("no_payment_method"):
                    results["no_payment_method"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(
                        {"subscription_id": subscription.id, "error": result.get("error", "Unknown error")}
                    )
            except Exception as e:
                logger.error(f"Error processing auto payment for subscription {subscription.id}: {str(e)}")
                results["failed"] += 1
                results["errors"].append({"subscription_id": subscription.id, "error": str(e)})

        return results

    async def _process_single_auto_payment(self, subscription: Subscription) -> dict[str, Any]:
        """
        Обработать автоплатеж для одной подписки

        Args:
            subscription: Подписка для обработки

        Returns:
            Dict с результатом обработки
        """
        # Получаем пользователя
        user = await self.uow.users.get_by_id_or_raise(subscription.user_id)

        # Проверяем наличие сохраненного платежного метода
        if not user.saved_payment_method_id:
            # Нет сохраненного метода - создаем новый платеж
            return await self._create_new_payment_for_renewal(subscription)

        # Есть сохраненный метод - проводим автосписание
        return await self._process_auto_charge(subscription, user.saved_payment_method_id)

    async def _create_new_payment_for_renewal(self, subscription: Subscription) -> dict[str, Any]:
        """
        Создать новый платеж для продления подписки (если нет сохраненного метода)

        Args:
            subscription: Подписка для продления

        Returns:
            Dict с результатом
        """
        try:
            # Получаем план подписки для определения условий
            await self.uow.subscription_plans.get_by_id_or_raise(subscription.plan_id)

            # Создаем запрос на создание подписки с платежом
            # Используем стандартный return_url из настроек
            from app.core.config import settings

            return_url = settings.YOOKASSA_CALLBACK_RETURN_URL

            orchestrator = SubscriptionOrchestratorService(self.uow)
            request = SubscriptionWithPaymentRequest(
                user_id=subscription.user_id, plan_id=subscription.plan_id, return_url=return_url
            )

            result = await orchestrator.create_subscription_with_payment(request)

            # Отправляем уведомление пользователю
            await self._send_notification(
                subscription.user_id,
                f"Для продления подписки необходимо оплатить. Перейдите по ссылке: {result.confirmation_url}",
            )

            return {
                "success": True,
                "no_payment_method": True,
                "message": "New payment created",
                "payment_id": result.payment_id,
                "confirmation_url": result.confirmation_url,
            }
        except Exception as e:
            logger.error(f"Error creating new payment for subscription {subscription.id}: {str(e)}")
            return {"success": False, "no_payment_method": True, "error": str(e)}

    async def _process_auto_charge(self, subscription: Subscription, payment_method_id: str) -> dict[str, Any]:
        """
        Провести автосписание с использованием сохраненного платежного метода

        Args:
            subscription: Подписка для продления
            payment_method_id: ID сохраненного платежного метода в YooKassa

        Returns:
            Dict с результатом
        """
        try:
            # Получаем план для определения суммы
            plan = await self.uow.subscription_plans.get_by_id_or_raise(subscription.plan_id)

            # Создаем платеж через YooKassa с сохраненным методом
            # Для автосписания используем одностадийный платеж
            idempotency_key = str(uuid.uuid4())

            from app.core.config import settings
            from app.schemas.yookassa import YookassaPaymentRequest

            yookassa_request = YookassaPaymentRequest(
                amount_value=str(plan.price),
                description=f"Автоплатеж за продление подписки {subscription.id}",
                return_url=settings.YOOKASSA_CALLBACK_RETURN_URL,
                payment_method_id=payment_method_id,  # Передаем сохраненный платежный метод
            )

            # Создаем одностадийный платеж (capture=True)
            yookassa_payment = self.uow.yookassa_client.create_payment(
                request=yookassa_request, idempotency_key=idempotency_key
            )

            # Создаем запись о платеже в БД
            db_payment = Payment(
                user_id=subscription.user_id,
                subscription_id=subscription.id,
                yookassa_payment_id=yookassa_payment.id,
                amount=plan.price,
                currency="RUB",
                status=PaymentStatus.pending.value,
                attempt_number=1,
                idempotency_key=idempotency_key,
                payment_method="auto_payment",
            )
            created_payment = await self.uow.payments.create(db_payment)

            # Проверяем статус платежа
            if yookassa_payment.status == "succeeded":
                # Платеж успешен - продлеваем подписку
                await self._renew_subscription(subscription, plan.duration_days)

                # Обновляем статус платежа в БД
                created_payment.status = PaymentStatus.succeeded.value
                await self.uow.payments.update(created_payment)

                # Обновляем объект subscription из БД для получения актуальных дат
                subscription = await self.uow.subscriptions.get_by_id_or_raise(subscription.id)

                # Отправляем уведомление с актуальной датой окончания
                await self._send_notification(
                    subscription.user_id,
                    f"Автоплатеж успешно проведен. Подписка продлена до {subscription.end_date.strftime('%d.%m.%Y')}",
                )

                return {
                    "success": True,
                    "message": "Auto payment succeeded",
                    "payment_id": created_payment.id,
                    "subscription_extended": True,
                }
            elif yookassa_payment.status == "pending":
                # Платеж в обработке - ждем webhook
                return {
                    "success": True,
                    "message": "Auto payment pending",
                    "payment_id": created_payment.id,
                    "status": "pending",
                }
            else:
                # Платеж не прошел
                created_payment.status = yookassa_payment.status
                await self.uow.payments.update(created_payment)

                # Отправляем уведомление об ошибке
                await self._send_notification(
                    subscription.user_id,
                    f"Автоплатеж не прошел. Статус: {yookassa_payment.status}. Пожалуйста, обновите платежный метод.",
                )

                return {
                    "success": False,
                    "error": f"Payment status: {yookassa_payment.status}",
                    "payment_id": created_payment.id,
                }

        except Exception as e:
            logger.error(f"Error processing auto charge for subscription {subscription.id}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _renew_subscription(self, subscription: Subscription, duration_days: int) -> None:
        """
        Продлить подписку на указанное количество дней с обновлением дат

        Args:
            subscription: Подписка для продления
            duration_days: Количество дней для продления
        """
        now = datetime.now(timezone.utc)

        # Если подписка уже истекла, начинаем новую подписку с сегодня
        if subscription.end_date <= now:
            subscription.start_date = now
            subscription.end_date = now + timedelta(days=duration_days)
            logger.info(f"Subscription {subscription.id} expired, starting new period from {subscription.start_date}")
        else:
            # Если подписка еще активна, продлеваем от текущей даты окончания
            # start_date остается прежним, обновляем только end_date
            old_end_date = subscription.end_date
            subscription.end_date = subscription.end_date + timedelta(days=duration_days)
            logger.info(f"Subscription {subscription.id} extended from {old_end_date} to {subscription.end_date}")

        # Обновляем статус и дату обновления
        subscription.status = SubscriptionStatus.active.value
        subscription.updated_at = now

        # Сохраняем изменения в БД
        await self.uow.subscriptions.update(subscription)

        # Обновляем объект из БД для гарантии актуальности данных
        # (особенно важно для updated_at, который может быть установлен на уровне БД)
        await self.uow.session.refresh(subscription)

        logger.info(
            f"Subscription {subscription.id} renewed: start_date={subscription.start_date}, "
            f"end_date={subscription.end_date}, status={subscription.status}"
        )

    async def _send_notification(self, user_id: int, message: str) -> None:
        """
        Отправить уведомление пользователю

        Args:
            user_id: ID пользователя
            message: Текст сообщения
        """
        try:
            # Импортируем задачу Celery для отправки уведомлений
            from app.tasks.notification import send_notification

            # Отправляем асинхронно через Celery
            send_notification.delay(user_id, message, "payment")
        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {str(e)}")

    async def send_payment_reminder_notifications(self) -> dict[str, Any]:
        """
        Отправить уведомления пользователям о предстоящем платеже завтра

        Returns:
            Dict с результатами
        """
        subscriptions = await self.uow.subscriptions.get_subscriptions_ending_tomorrow()

        results = {"total": len(subscriptions), "sent": 0, "failed": 0, "errors": []}

        for subscription in subscriptions:
            try:
                # Получаем план для информации о сумме
                plan = await self.uow.subscription_plans.get_by_id_or_raise(subscription.plan_id)

                user = await self.uow.users.get_by_id_or_raise(subscription.user_id)

                # Формируем сообщение
                if user.saved_payment_method_id:
                    message = (
                        f"Напоминание: завтра будет автоматически списана сумма "
                        f"{plan.price} RUB за продление подписки. "
                        f"Если вы хотите отменить автоплатеж, пожалуйста, сделайте это сейчас."
                    )
                else:
                    message = (
                        f"Напоминание: завтра истекает ваша подписка. "
                        f"Для продления необходимо будет создать новый платеж на сумму "
                        f"{plan.price} RUB."
                    )

                await self._send_notification(subscription.user_id, message)
                results["sent"] += 1

            except Exception as e:
                logger.error(f"Error sending reminder for subscription {subscription.id}: {str(e)}")
                results["failed"] += 1
                results["errors"].append({"subscription_id": subscription.id, "error": str(e)})

        return results

    async def _is_subscription_already_extended(self, subscription_id: int) -> bool:
        """
        Проверить, не была ли подписка уже продлена.
        Используется для идемпотентности - если подписка уже продлена,
        не нужно продлевать повторно.

        Args:
            subscription_id: ID подписки

        Returns:
            True если подписка уже продлена, False иначе
        """
        subscription = await self.uow.subscriptions.get_by_id(subscription_id)
        if not subscription:
            return False

        # Если end_date больше чем сегодня, значит подписка уже продлена
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)

        # Подписка считается продленной, если end_date >= завтра
        return subscription.end_date >= tomorrow

    async def save_payment_method_from_webhook(self, user_id: int, payment_method_id: str) -> None:
        """
        Сохранить платежный метод напрямую из вебхука (когда уже известно, что пользователь дал согласие)

        Args:
            user_id: ID пользователя
            payment_method_id: ID сохраненного платежного метода в YooKassa
        """
        try:
            await self.uow.users.update_saved_payment_method(user_id, payment_method_id)
            logger.info(
                f"Saved payment method ID for user {user_id} from webhook: {payment_method_id} "
                f"(user consented to auto payments)"
            )
        except Exception as e:
            logger.error(f"Error saving payment method from webhook for user {user_id}: {str(e)}")

    async def save_payment_method_after_success(self, user_id: int, yookassa_payment_id: str) -> None:
        """
        Сохранить платежный метод после успешного платежа (fallback метод, когда нет данных из вебхука).
        ВАЖНО: Сохраняет только если пользователь явно дал согласие (payment_method.saved = true)

        Args:
            user_id: ID пользователя
            yookassa_payment_id: ID платежа в YooKassa
        """
        try:
            # Получаем информацию о платеже из YooKassa
            payment_info = self.uow.yookassa_client.get_payment(yookassa_payment_id)

            # Если платеж был успешным, проверяем согласие пользователя на сохранение метода
            if payment_info.status == "succeeded":
                # Извлекаем payment_method из ответа платежа
                payment_method = None
                payment_method_saved = False
                payment_method_id = None

                # Проверяем наличие payment_method в ответе
                if hasattr(payment_info, "payment_method") and payment_info.payment_method:
                    payment_method = payment_info.payment_method
                elif isinstance(payment_info, dict) and payment_info.get("payment_method"):
                    payment_method = payment_info.get("payment_method")

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
                    elif isinstance(payment_method, str):
                        payment_method_id = payment_method

                # Сохраняем только если пользователь дал согласие (saved=True) и есть ID метода
                if payment_method_saved and payment_method_id:
                    await self.uow.users.update_saved_payment_method(user_id, payment_method_id)
                    logger.info(
                        f"Saved payment method ID for user {user_id} from API: {payment_method_id} "
                        f"(user consented to auto payments)"
                    )
                elif not payment_method_saved:
                    logger.info(
                        f"Payment {yookassa_payment_id} succeeded but user did not consent to save payment method "
                        f"(saved=False or missing). Payment method will not be saved for user {user_id}"
                    )
                elif payment_method_saved and not payment_method_id:
                    logger.warning(
                        f"Payment {yookassa_payment_id} has saved=True but no payment_method.id found. "
                        f"Cannot save payment method for user {user_id}"
                    )
                else:
                    logger.warning(
                        f"Payment {yookassa_payment_id} succeeded but no payment_method found. "
                        f"Cannot save payment method for user {user_id}"
                    )
        except Exception as e:
            logger.error(f"Error saving payment method for user {user_id}: {str(e)}")
