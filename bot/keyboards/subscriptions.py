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
    def confirm_subscription_keyboard(plan_id):
        """Кнопки для подтверждения подписки"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Оформить", callback_data=f"confirm_subscribe_{plan_id}"),
                    InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_subscribe"),
                ]
            ]
        )

    @staticmethod
    def cancel_subscription_keyboard(sub_id):
        """Кнопки для отмены подписки"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="❌ Отменить подписку", callback_data=f"cancel_sub_{sub_id}"),
                    InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu"),
                ]
            ]
        )

    @staticmethod
    def active_subscription_keyboard(sub_id):
        """Кнопки для активной подписки (отмена подписки)"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="❌ Отменить подписку", callback_data=f"cancel_sub_{sub_id}"),
                    InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu"),
                ],
            ]
        )
