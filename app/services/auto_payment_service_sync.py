"""
Синхронный Auto Payment Service - сервис для автоматических платежей подписок.
Используется в Celery задачах.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.auto_payment_config import auto_payment_config
from app.core.config import settings
from app.core.enums import PaymentStatus, SubscriptionStatus
from app.core.logger import logger
from app.database.sync_unit_of_work import SyncUnitOfWork
from app.models import Payment, Subscription


class AutoPaymentServiceSync:
    """Синхронный сервис для обработки автоматических платежей подписок (для Celery)"""

    def __init__(self, uow: SyncUnitOfWork):
        self.uow = uow

    def process_single_subscription_payment(self, subscription_id: int) -> dict[str, Any]:
        """
        Обработать платеж для одной подписки.

        ВАЖНО: Используем SELECT FOR UPDATE для защиты от гонок.
        ВАЖНО: Проверяем идемпотентность - предотвращаем двойные платежи.

        Логика:
        - Если есть saved_payment_method_id: создает платеж и возвращает payment_id для запуска попыток
        - Если нет saved_payment_method_id: создает платеж со ссылкой, отправляет уведомление, ставит cancelled

        Args:
            subscription_id: ID подписки для обработки

        Returns:
            Dict с результатом обработки
        """
        # 🔒 Блокируем строку подписки для безопасного платежа
        locked_subscription = self.uow.subscriptions.get_for_payment_with_lock(subscription_id)

        if not locked_subscription:
            return {"success": False, "error": "subscription_not_found"}

        # Проверяем статус после блокировки
        if locked_subscription.status in [
            SubscriptionStatus.cancelled.value,
            SubscriptionStatus.cancelled_waiting.value,
        ]:
            return {
                "success": False,
                "error": "subscription_cancelled",
                "message": "Subscription was cancelled, no auto payment needed",
            }

        # 🔍 ИДЕМПОТЕНТНОСТЬ: Проверяем, не была ли подписка уже продлена
        if self.uow.subscriptions.is_subscription_already_extended(locked_subscription.id):
            logger.info(f"Subscription {locked_subscription.id} already extended, skipping payment")
            return {"success": True, "skipped": True, "message": "Subscription already extended, payment not needed"}

        # 🆕 НОВАЯ ПРОВЕРКА: Проверяем, был ли применен промокод сегодня
        if self._was_promotion_applied_today(locked_subscription):
            logger.info(
                f"Subscription {locked_subscription.id} had promotion applied today, "
                f"skipping auto payment to avoid double charge"
            )
            return {
                "success": True,
                "skipped": True,
                "message": "Promotion applied today, auto payment skipped",
            }

        # 🔍 ИДЕМПОТЕНТНОСТЬ: Проверяем существующие платежи за сегодня
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        idempotency_key = f"auto_payment_{locked_subscription.id}_{today_str}"

        existing_payment = self.uow.payments.get_payment_by_idempotency_key(idempotency_key)
        if existing_payment:
            logger.info(
                f"Payment with idempotency_key {idempotency_key} already exists "
                f"(payment_id={existing_payment.id}), skipping duplicate"
            )
            return {
                "success": True,
                "skipped": True,
                "message": "Payment already exists",
                "payment_id": existing_payment.id,
            }

        # Получаем пользователя
        user = self.uow.users.get_by_id_or_raise(locked_subscription.user_id)

        # Проверяем наличие сохраненного платежного метода
        if not user.saved_payment_method_id:
            # Нет сохраненного метода - создаем платеж со ссылкой
            return self._create_payment_without_method(locked_subscription)

        # Есть сохраненный метод - создаем платеж для автосписания
        return self._create_payment_for_auto_charge(locked_subscription, user.saved_payment_method_id)

    def _create_payment_without_method(self, subscription: Subscription) -> dict[str, Any]:
        """
        Создать платеж для подписки без сохраненного метода.
        Отправляет ссылку на оплату и ставит статус cancelled.

        Args:
            subscription: Подписка для продления

        Returns:
            Dict с результатом
        """
        try:
            plan = self.uow.subscription_plans.get_by_id_or_raise(subscription.plan_id)
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            idempotency_key = f"auto_payment_{subscription.id}_{today_str}"

            # Проверяем еще раз на случай race condition
            existing_payment = self.uow.payments.get_payment_by_idempotency_key(idempotency_key)
            if existing_payment:
                return {
                    "success": True,
                    "skipped": True,
                    "message": "Payment already exists",
                    "payment_id": existing_payment.id,
                }

            from app.schemas.yookassa import YookassaPaymentRequest

            yookassa_request = YookassaPaymentRequest(
                amount_value=str(plan.price),
                description=f"Платеж за продление подписки {subscription.id}",
                return_url=settings.YOOKASSA_CALLBACK_RETURN_URL,
            )

            # Создаем платеж в YooKassa
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
                payment_method="manual",
            )

            try:
                created_payment = self.uow.payments.create_payment(db_payment)
            except Exception as e:
                from sqlalchemy.exc import IntegrityError

                if isinstance(e, IntegrityError) and "idempotency_key" in str(e):
                    existing_payment = self.uow.payments.get_payment_by_idempotency_key(idempotency_key)
                    if existing_payment:
                        return {
                            "success": True,
                            "skipped": True,
                            "message": "Payment already exists (race condition)",
                            "payment_id": existing_payment.id,
                        }
                raise

            # Обновляем статус подписки на cancelled
            subscription.status = SubscriptionStatus.cancelled.value
            subscription.updated_at = datetime.now(timezone.utc)
            self.uow.subscriptions.update_subscription(subscription)

            # Отправляем уведомление пользователю (1 раз)
            confirmation_url = (
                yookassa_payment.confirmation.confirmation_url if hasattr(yookassa_payment, "confirmation") else None
            )
            if confirmation_url:
                self._send_notification(
                    subscription.user_id,
                    f"Для продления подписки необходимо оплатить. Перейдите по ссылке: {confirmation_url}",
                )

            return {
                "success": True,
                "no_payment_method": True,
                "message": "Payment created, subscription cancelled",
                "payment_id": created_payment.id,
                "confirmation_url": confirmation_url,
            }
        except Exception as e:
            logger.error(f"Error creating payment without method for subscription {subscription.id}: {str(e)}")
            return {"success": False, "no_payment_method": True, "error": str(e)}

    def _create_payment_for_auto_charge(self, subscription: Subscription, payment_method_id: str) -> dict[str, Any]:
        """
        Создать платеж для автосписания с сохраненным методом.

        Args:
            subscription: Подписка для продления
            payment_method_id: ID сохраненного платежного метода в YooKassa

        Returns:
            Dict с результатом (содержит payment_id для запуска попыток)
        """
        try:
            plan = self.uow.subscription_plans.get_by_id_or_raise(subscription.plan_id)
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            idempotency_key = f"auto_payment_{subscription.id}_{today_str}"

            # Проверяем еще раз на случай race condition
            existing_payment = self.uow.payments.get_payment_by_idempotency_key(idempotency_key)
            if existing_payment:
                return {
                    "success": True,
                    "skipped": True,
                    "message": "Payment already exists",
                    "payment_id": existing_payment.id,
                }

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

            try:
                created_payment = self.uow.payments.create_payment(db_payment)
            except Exception as e:
                from sqlalchemy.exc import IntegrityError

                if isinstance(e, IntegrityError) and "idempotency_key" in str(e):
                    existing_payment = self.uow.payments.get_payment_by_idempotency_key(idempotency_key)
                    if existing_payment:
                        return {
                            "success": True,
                            "skipped": True,
                            "message": "Payment already exists (race condition)",
                            "payment_id": existing_payment.id,
                        }
                raise

            return {
                "success": True,
                "message": "Payment created for auto charge",
                "payment_id": created_payment.id,
                "needs_retry": True,  # Флаг для запуска попыток
            }
        except Exception as e:
            logger.error(f"Error creating payment for auto charge subscription {subscription.id}: {str(e)}")
            return {"success": False, "error": str(e)}

    def retry_auto_payment_attempt(self, payment_id: int, attempt: int) -> dict[str, Any]:
        """
        Попытка автосписания для платежа.

        ВАЖНО: Используем SELECT FOR UPDATE для защиты от гонок с webhook.
        ВАЖНО: Проверяем статус платежа перед обновлением - не перезаписываем succeeded.

        Args:
            payment_id: ID платежа
            attempt: Номер попытки (начинается с 1)

        Returns:
            Dict с результатом попытки
        """
        try:
            # 🔒 Блокируем платеж для безопасной обработки (защита от гонок с webhook)
            payment = self.uow.payments.get_for_processing_with_lock(payment_id)
            if not payment:
                return {"success": False, "error": "payment_not_found"}

            # 🔍 ИДЕМПОТЕНТНОСТЬ: Проверяем, не был ли платеж уже успешно обработан
            if payment.status == PaymentStatus.succeeded.value:
                logger.info(
                    f"Payment {payment_id} already succeeded (possibly processed by webhook), skipping retry attempt"
                )
                # Проверяем, была ли подписка продлена
                subscription = self.uow.subscriptions.get_subscription_by_id_or_raise(payment.subscription_id)
                if self.uow.subscriptions.is_subscription_already_extended(subscription.id):
                    return {
                        "success": True,
                        "skipped": True,
                        "message": "Payment already succeeded and subscription extended",
                    }
                # Если платеж succeeded, но подписка не продлена - продлеваем
                plan = self.uow.subscription_plans.get_by_id_or_raise(subscription.plan_id)
                self._renew_subscription(subscription, plan.duration_days)
                subscription = self.uow.subscriptions.get_subscription_by_id_or_raise(subscription.id)
                self._send_notification(
                    subscription.user_id,
                    f"✅ Автоплатеж успешно проведен. Подписка продлена до {subscription.end_date.strftime('%d.%m.%Y')}",
                )
                return {"success": True, "final": True, "message": "Payment succeeded, subscription extended"}

            # Получаем подписку с блокировкой
            subscription = self.uow.subscriptions.get_for_payment_with_lock(payment.subscription_id)
            if not subscription:
                return {"success": False, "error": "subscription_not_found"}

            # Проверяем статус подписки
            if subscription.status in [
                SubscriptionStatus.cancelled.value,
                SubscriptionStatus.cancelled_waiting.value,
            ]:
                return {"success": False, "error": "subscription_cancelled"}

            # Проверяем, не была ли подписка уже продлена
            if self.uow.subscriptions.is_subscription_already_extended(subscription.id):
                logger.info(f"Subscription {subscription.id} already extended, skipping payment attempt")
                return {"success": True, "skipped": True, "message": "Subscription already extended"}

            # Получаем пользователя
            user = self.uow.users.get_by_id_or_raise(payment.user_id)

            if not user.saved_payment_method_id:
                # Нет сохраненного метода - помечаем как failed
                payment.status = PaymentStatus.failed.value
                payment.attempt_number = attempt
                self.uow.payments.update_payment(payment)
                return {"success": False, "error": "no_payment_method"}

            # Проверяем статус платежа в YooKassa
            try:
                yookassa_payment = self.uow.yookassa_client.get_payment(payment.yookassa_payment_id)

                # 🔍 ИДЕМПОТЕНТНОСТЬ: Обновляем статус только если он изменился
                # Не перезаписываем succeeded, если платеж уже был обработан
                old_status = payment.status
                if yookassa_payment.status != payment.status:
                    payment.status = yookassa_payment.status
                    logger.info(f"Payment {payment_id} status updated from {old_status} to {yookassa_payment.status}")
                payment.attempt_number = attempt
                self.uow.payments.update_payment(payment)

                if yookassa_payment.status == "succeeded":
                    # Платеж успешен - продлеваем подписку
                    plan = self.uow.subscription_plans.get_by_id_or_raise(subscription.plan_id)
                    self._renew_subscription(subscription, plan.duration_days)

                    # Отправляем финальное уведомление
                    subscription = self.uow.subscriptions.get_subscription_by_id_or_raise(subscription.id)
                    self._send_notification(
                        subscription.user_id,
                        f"✅ Автоплатеж успешно проведен. Подписка продлена до {subscription.end_date.strftime('%d.%m.%Y')}",
                    )

                    return {"success": True, "final": True, "message": "Auto payment succeeded, subscription extended"}
                elif yookassa_payment.status == "pending":
                    # Платеж все еще в процессе
                    return {"success": True, "pending": True, "message": "Payment still pending"}
                else:
                    # Платеж не прошел
                    payment.status = PaymentStatus.failed.value
                    self.uow.payments.update_payment(payment)

                    # Проверяем, исчерпаны ли все попытки
                    config = auto_payment_config.get_config()
                    max_attempts = config["max_attempts"]
                    if attempt >= max_attempts:
                        # Все попытки исчерпаны - ставим cancelled_waiting
                        subscription.status = SubscriptionStatus.cancelled_waiting.value
                        subscription.updated_at = datetime.now(timezone.utc)
                        self.uow.subscriptions.update_subscription(subscription)

                        # Отправляем финальное уведомление
                        self._send_notification(
                            subscription.user_id,
                            "❌ Не удалось продлить подписку после всех попыток оплаты. "
                            "Подписка будет отменена в конце дня.",
                        )

                        return {
                            "success": False,
                            "final": True,
                            "message": "All attempts failed, subscription set to cancelled_waiting",
                        }
                    else:
                        # Еще есть попытки
                        return {
                            "success": False,
                            "final": False,
                            "message": f"Payment failed, attempt {attempt}/{max_attempts}",
                        }

            except Exception as e:
                logger.error(f"Error checking payment status from YooKassa: {str(e)}")
                payment.attempt_number = attempt
                payment.status = PaymentStatus.failed.value
                self.uow.payments.update_payment(payment)

                # Проверяем, исчерпаны ли все попытки
                config = auto_payment_config.get_config()
                max_attempts = config["max_attempts"]
                if attempt >= max_attempts:
                    subscription.status = SubscriptionStatus.cancelled_waiting.value
                    subscription.updated_at = datetime.now(timezone.utc)
                    self.uow.subscriptions.update_subscription(subscription)

                    self._send_notification(
                        subscription.user_id,
                        "❌ Не удалось продлить подписку после всех попыток оплаты. "
                        "Подписка будет отменена в конце дня.",
                    )

                    return {
                        "success": False,
                        "final": True,
                        "error": str(e),
                        "message": "All attempts failed, subscription set to cancelled_waiting",
                    }
                else:
                    return {"success": False, "final": False, "error": str(e)}

        except Exception as e:
            logger.error(f"Error in retry_auto_payment_attempt for payment {payment_id}: {str(e)}")
            return {"success": False, "error": str(e)}

    def process_cancelled_waiting_subscriptions(self) -> dict[str, Any]:
        """
        Обработать все подписки со статусом cancelled_waiting.
        Переводит их в статус cancelled.

        Returns:
            Dict с результатами обработки
        """
        # Получаем все подписки со статусом cancelled_waiting
        subscriptions = self.uow.subscriptions.get_subscriptions_by_status(SubscriptionStatus.cancelled_waiting.value)

        results = {"total": len(subscriptions), "processed": 0, "errors": []}

        for subscription in subscriptions:
            try:
                # Блокируем подписку
                locked_subscription = self.uow.subscriptions.get_for_payment_with_lock(subscription.id)
                if not locked_subscription:
                    results["errors"].append({"subscription_id": subscription.id, "error": "subscription_not_found"})
                    continue

                # Проверяем статус (может быть изменен вручную)
                if locked_subscription.status != SubscriptionStatus.cancelled_waiting.value:
                    logger.info(
                        f"Subscription {locked_subscription.id} status changed from cancelled_waiting "
                        f"to {locked_subscription.status}, skipping"
                    )
                    continue

                # Переводим в cancelled
                locked_subscription.status = SubscriptionStatus.cancelled.value
                locked_subscription.updated_at = datetime.now(timezone.utc)
                self.uow.subscriptions.update_subscription(locked_subscription)

                results["processed"] += 1
                logger.info(f"Subscription {locked_subscription.id} moved from cancelled_waiting to cancelled")

            except Exception as e:
                logger.error(f"Error processing cancelled_waiting subscription {subscription.id}: {str(e)}")
                results["errors"].append({"subscription_id": subscription.id, "error": str(e)})

        return results

    def _renew_subscription(self, subscription: Subscription, duration_days: int) -> None:
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
            old_end_date = subscription.end_date
            subscription.end_date = subscription.end_date + timedelta(days=duration_days)
            logger.info(f"Subscription {subscription.id} extended from {old_end_date} to {subscription.end_date}")

        # Обновляем статус и дату обновления
        subscription.status = SubscriptionStatus.active.value
        subscription.updated_at = now

        # Сохраняем изменения в БД
        self.uow.subscriptions.update_subscription(subscription)

        logger.info(
            f"Subscription {subscription.id} renewed: start_date={subscription.start_date}, "
            f"end_date={subscription.end_date}, status={subscription.status}"
        )

    def _send_notification(self, user_id: int, message: str) -> None:
        """
        Отправить уведомление пользователю в Telegram

        Args:
            user_id: ID пользователя (используется для получения telegram_id)
            message: Текст сообщения
        """
        try:
            user = self.uow.users.get_by_id(user_id)
            if not user:
                logger.warning(f"User {user_id} not found, cannot send notification")
                return

            if not user.telegram_id:
                logger.warning(f"User {user_id} has no telegram_id, cannot send notification")
                return

            from app.core.telegram_notifier import telegram_notifier

            success = telegram_notifier.send_notification_to_user(telegram_id=user.telegram_id, message=message)

            if not success:
                logger.warning(
                    f"Failed to send Telegram notification to user {user_id} (telegram_id={user.telegram_id})"
                )
            else:
                logger.debug(
                    f"Telegram notification sent successfully to user {user_id} (telegram_id={user.telegram_id})"
                )

        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {str(e)}", exc_info=True)

    def send_payment_reminder_notifications(self) -> dict[str, Any]:
        """
        Отправить уведомления пользователям о предстоящем платеже завтра

        Returns:
            Dict с результатами
        """
        subscriptions = self.uow.subscriptions.get_subscriptions_ending_tomorrow()

        results = {"total": len(subscriptions), "sent": 0, "failed": 0, "errors": []}

        for subscription in subscriptions:
            try:
                plan = self.uow.subscription_plans.get_by_id_or_raise(subscription.plan_id)
                user = self.uow.users.get_by_id_or_raise(subscription.user_id)

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

                self._send_notification(subscription.user_id, message)
                results["sent"] += 1

            except Exception as e:
                logger.error(f"Error sending reminder for subscription {subscription.id}: {str(e)}")
                results["failed"] += 1
                results["errors"].append({"subscription_id": subscription.id, "error": str(e)})

        return results

    def _was_promotion_applied_today(self, subscription: Subscription) -> bool:
        """
        Проверить, был ли применен промокод к подписке сегодня.

        Логика: Если у подписки есть promotion_id и updated_at = сегодня,
        значит промокод был применен сегодня.

        Args:
            subscription: Подписка для проверки

        Returns:
            True если промокод был применен сегодня, False иначе
        """
        if not subscription.promotion_id:
            return False

        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        # Проверяем, что подписка обновлена сегодня и имеет promotion_id
        return (
            subscription.updated_at >= today_start
            and subscription.updated_at < today_end
            and subscription.promotion_id is not None
        )
