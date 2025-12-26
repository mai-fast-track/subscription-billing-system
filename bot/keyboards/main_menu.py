from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class MainMenuKeyboard:
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
