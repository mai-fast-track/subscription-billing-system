from datetime import datetime, timezone


class Formatters:
    """Форматирование текста для сообщений"""

    @staticmethod
    def format_subscription_plan(plan) -> str:
        """Форматировать план подписки"""
        return (
            f"📌 {plan.name}\n"
            f"💰 Цена: {plan.price} ₽\n"
            f"📅 Длительность: {plan.duration_days} дней\n"
            f"📝 Описание: {plan.features or 'Нет описания'}"
        )

    @staticmethod
    def format_all_plans(plans) -> str:
        """Форматировать список всех планов"""
        if not plans:
            return "❌ Планы подписок не найдены"

        text = "💳 Доступные планы:\n\n"
        for i, plan in enumerate(plans, 1):
            text += f"{i}. {plan.name} - {plan.price} ₽\n"
        return text

    @staticmethod
    def format_subscription(subscription) -> str:
        """Форматировать подписку"""
        return (
            f"✅ Подписка активирована!\n\n"
            f"Начало: {subscription.start_date.strftime('%d.%m.%Y')}\n"
            f"Следующее списание: {subscription.end_date.strftime('%d.%m.%Y')}\n"
        )

    @staticmethod
    def format_active_subscription(subscription, plan) -> str:
        """Форматировать активную подписку"""
        end_date = subscription.end_date
        if isinstance(end_date, str):
            from dateutil import parser

            end_date = parser.parse(end_date)

        now_utc = datetime.now(timezone.utc)
        days_left = (end_date - now_utc).days if hasattr(end_date, "__sub__") else 0

        # Проверяем статус подписки
        status = getattr(subscription, "status", "active")

        # cancelled_waiting только для автоплатежей
        # При отмене пользователем всегда ставится cancelled
        if status == "cancelled":
            if hasattr(end_date, "__sub__") and end_date > now_utc:
                status_text = "⏸️ ОТМЕНЕНА (активна до конца периода)"
            else:
                status_text = "❌ ОТМЕНЕНА"
        elif status == "cancelled_waiting":
            # Статус от автоплатежей - показываем как отмененную, но активную
            status_text = "⏸️ ОТМЕНЕНА (активна до конца периода)"
        else:
            status_text = "✅ АКТИВНА"

        end_date_str = end_date.strftime("%d.%m.%Y %H:%M") if hasattr(end_date, "strftime") else str(end_date)

        return f"{status_text}\n\nДо: {end_date_str}\n⏱️ Осталось: {days_left} дней\n"

    @staticmethod
    def format_payment(payment: dict) -> str:
        """Форматировать платёж"""
        if not isinstance(payment, dict):
            try:
                if hasattr(payment, "model_dump"):
                    payment = payment.model_dump()
                elif hasattr(payment, "dict"):
                    payment = payment.dict()
                else:
                    payment = dict(payment) if payment else {}
            except Exception:
                return "❌ Ошибка форматирования платежа: неверный формат данных"

        amount = payment.get("amount", 0)
        currency = payment.get("currency", "RUB")
        status = payment.get("status", "unknown")
        created_at = payment.get("created_at")
        subscription_plan_name = payment.get("subscription_plan_name")
        subscription_status = payment.get("subscription_status")
        payment_method = payment.get("payment_method")

        # Форматируем дату (только дата, без времени)
        if created_at:
            try:
                if isinstance(created_at, str):
                    from dateutil import parser

                    date_obj = parser.parse(created_at)
                elif hasattr(created_at, "strftime"):
                    date_obj = created_at
                else:
                    date_str = "N/A"
                if "date_obj" in locals():
                    date_str = date_obj.strftime("%d.%m.%Y")  # Убрали время
                else:
                    date_str = "N/A"
            except Exception:
                date_str = "N/A"
        else:
            date_str = "N/A"


        status_map = {
            "succeeded": ("✅", "Успешно"),
            "pending": ("⏳", "Ожидание"),
            "failed": ("❌", "Ошибка"),
            "cancelled": ("🚫", "Отменено"),
            "waiting_for_capture": ("⏸️", "Ожидает подтверждения"),
        }
        emoji, status_text = status_map.get(status, ("❓", "Неизвестно"))
        status_display = f"{emoji} {status_text}"


        method_display = ""
        if payment_method:

            method_translations = {
                "card_change": "Смена карты",
                "auto_payment": "Автоплатеж",
                "manual": "Ручной платеж",
            }
            method_text = method_translations.get(payment_method, payment_method)
            method_display = f"\n💳 Метод: {method_text}"


        subscription_info = ""
        if subscription_plan_name:
            subscription_info = f"\n📋 План: {subscription_plan_name}"
        if subscription_status:
            subscription_info += f" ({subscription_status})"


        refund_info = ""
        refund_amount = payment.get("refund_amount")
        refund_status = payment.get("refund_status")
        if refund_amount is not None and refund_amount > 0:

            refund_status_translations = {
                "succeeded": "✅ Возвращен",
                "pending": "⏳ Ожидает возврата",
                "failed": "❌ Ошибка возврата",
                "cancelled": "🚫 Отменен",
            }
            refund_status_text = refund_status_translations.get(refund_status, refund_status or "⏳ Ожидает")
            refund_info = f"\n💸 Возврат: {refund_amount} {currency} ({refund_status_text})"

        return (
            f"💰 Сумма: {amount} {currency}\n"
            f"📅 Дата: {date_str}\n"
            f"ℹ️ Статус: {status_display}{method_display}{subscription_info}{refund_info}"
        )

    @staticmethod
    def format_payments_list(payments: list[dict], title: str = "Платежи") -> str:
        """Форматировать список платежей"""
        if not payments:
            return "❌ Нет платежей"

        text = f"💰 <b>{title}:</b>\n\n"
        for i, payment in enumerate(payments, 1):
            try:
                text += f"{i}. {Formatters.format_payment(payment)}\n\n"
            except Exception as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(f"Error formatting payment {i}: {e}")
                continue
        return text

    @staticmethod
    def format_promo(promo) -> str:
        """Форматировать промокод"""
        return (
            f"🎁 <b>{promo.code}</b>\n"
            f"Скидка: <b>{promo.discount}%</b>\n"
            f"Действителен до: {promo.expiry_date.strftime('%d.%m.%Y') if promo.expiry_date else 'Бесконечно'}\n"
        )

    @staticmethod
    def format_error(error: str) -> str:
        """Форматировать ошибку"""
        return f"❌ <b>Ошибка:</b>\n{error}"

    @staticmethod
    def format_success(message: str) -> str:
        """Форматировать успешное сообщение"""
        return f"✅ <b>Успешно!</b>\n{message}"
