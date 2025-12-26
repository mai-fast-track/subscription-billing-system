from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class SubscriptionKeyboards:
    """Кнопки для управления подписками"""

    @staticmethod
    def subscription_plans_keyboard(plans):
        """Кнопки для выбора плана"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])

        for plan in plans:
            keyboard.inline_keyboard.append(
                [InlineKeyboardButton(text=f"📌 {plan.name} ({plan.price} ₽)", callback_data=f"subscribe_{plan.id}")]
            )

        keyboard.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")])

        return keyboard

    @staticmethod
    def confirm_subscription_keyboard(plan_id, trial_eligible: bool = False):
        """Кнопки для подтверждения подписки

        Args:
            plan_id: ID плана
            trial_eligible: Доступен ли промопериод (показываем две кнопки если True)
        """
        if trial_eligible:
            # Две кнопки: промопериод и оплата
            return InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="🎁 Промопериод", callback_data=f"create_trial_{plan_id}"),
                        InlineKeyboardButton(text="💳 Оплатить", callback_data=f"confirm_subscribe_{plan_id}"),
                    ],
                    [
                        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_subscribe"),
                    ],
                    [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")],
                ]
            )
        else:
            # Одна кнопка: только оплата
            return InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✅ Оформить", callback_data=f"confirm_subscribe_{plan_id}"),
                        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_subscribe"),
                    ],
                    [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")],
                ]
            )

    @staticmethod
    def cancel_subscription_keyboard(sub_id):
        """Кнопки для отмены подписки"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="💳 Сменить карту", callback_data="change_payment_method"),
                    InlineKeyboardButton(text="❌ Отменить подписку", callback_data=f"cancel_sub_{sub_id}"),
                ],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")],
            ]
        )

    @staticmethod
    def choose_cancellation_type_keyboard(sub_id):
        """Кнопки для выбора типа отмены подписки"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⏸️ Отменить (активна до конца периода)",
                        callback_data=f"cancel_sub_no_refund_{sub_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Отменить с возвратом",
                        callback_data=f"cancel_sub_with_refund_{sub_id}",
                    )
                ],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="my_subscription")],
            ]
        )

    @staticmethod
    def active_subscription_keyboard(sub_id):
        """Кнопки для активной подписки (отмена подписки)"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="💳 Сменить карту", callback_data="change_payment_method"),
                    InlineKeyboardButton(text="❌ Отменить подписку", callback_data=f"cancel_sub_{sub_id}"),
                ],
                [
                    InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu"),
                ],
            ]
        )

    @staticmethod
    def main_menu_keyboard():
        """Главное меню"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📋 Планы подписок", callback_data="view_plans")],
                [InlineKeyboardButton(text="✅ Моя подписка", callback_data="my_subscription")],
                [InlineKeyboardButton(text="🎁 Промокоды", callback_data="promo_menu")],
                [InlineKeyboardButton(text="💰 Платежи", callback_data="payment_menu")],
            ]
        )


class PromoKeyboards:
    """Кнопки для промокодов"""

    @staticmethod
    def promo_action_keyboard():
        """Выбор действия с промокодом"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🎁 Посмотреть промокоды", callback_data="view_promos")],
                [InlineKeyboardButton(text="✏️ Ввести промокод", callback_data="enter_promo")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")],
            ]
        )

    @staticmethod
    def confirm_promo_keyboard(promo_id):
        """Подтверждение применения промокода"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Применить", callback_data=f"apply_promo_{promo_id}"),
                    InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_promo"),
                ]
            ]
        )


class PaymentKeyboards:
    """Кнопки для платежей"""

    @staticmethod
    def back_to_menu_keyboard():
        """Кнопка возврата в главное меню"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")],
            ]
        )


class MainMenuKeyboard:
    """Главное меню кнопки"""

    @staticmethod
    def main_menu_keyboard():
        """Главное меню"""
        return SubscriptionKeyboards.main_menu_keyboard()
