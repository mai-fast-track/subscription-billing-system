from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


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
