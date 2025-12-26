"""
Promotion handlers for bot
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Add api-client to path
api_client_path = Path(__file__).parent.parent.parent / "api-client"
if str(api_client_path) not in sys.path:
    sys.path.insert(0, str(api_client_path))

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from billing_core_api_client.types import UNSET
from bot.keyboards.inline import SubscriptionKeyboards
from bot.services.auth_service import AuthService
from bot.services.promotion_service import PromotionService
from bot.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "promo_menu")
async def promo_menu(callback: CallbackQuery):
    """Показать список доступных промокодов"""
    await callback.answer()

    try:
        telegram_id = callback.from_user.id

        # Get or create user and get token
        auth_service = AuthService()
        user, token = await auth_service.authenticate_telegram_user(telegram_id)

        # Get available promotions
        promotion_service = PromotionService()
        promotions = await promotion_service.get_available_promotions(token.access_token)

        if not promotions:
            text = (
                "🎁 <b>Промокоды</b>\n\n"
                "❌ У вас нет доступных промокодов на данный момент.\n\n"
                "Проверьте позже или свяжитесь с поддержкой."
            )
            kb = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]]
            )
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
            return

        # Формируем список промокодов с кнопками
        text = "🎁 <b>Доступные промокоды:</b>\n\n"
        keyboard_buttons = []

        for promo in promotions:
            # Форматируем информацию о промокоде
            valid_until_str = ""
            if promo.valid_until is not None and promo.valid_until is not UNSET:
                if isinstance(promo.valid_until, datetime):
                    valid_until_str = promo.valid_until.strftime("%d.%m.%Y")
                else:
                    valid_until_str = str(promo.valid_until)

            promo_text = f"🎁 <b>{promo.code}</b>\n"
            promo_text += f"📝 {promo.name}\n"
            if promo.description:
                promo_text += f"💬 {promo.description}\n"
            promo_text += f"➕ Бонусных дней: <b>{promo.value}</b>\n"
            if valid_until_str:
                promo_text += f"📅 Действителен до: {valid_until_str}\n"
            if promo.max_uses:
                promo_text += f"🔢 Использований: {promo.current_uses}/{promo.max_uses}\n"
            promo_text += "\n"

            text += promo_text

            # Добавляем кнопку для применения промокода
            keyboard_buttons.append(
                [InlineKeyboardButton(text=f"✅ Применить {promo.code}", callback_data=f"apply_promo_{promo.id}")]
            )

        # Добавляем кнопку "Назад"
        keyboard_buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")])

        kb = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

    except Exception as e:
        logger.error(f"Error showing promotions menu: {e}")
        text = f"❌ Ошибка при загрузке промокодов: {str(e)}"
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]]
        )
        await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.startswith("apply_promo_"))
async def apply_promo(callback: CallbackQuery):
    """Применить промокод к активной подписке"""
    await callback.answer()

    try:
        # Извлекаем ID промокода из callback_data
        promo_id = int(callback.data.split("_")[-1])
        telegram_id = callback.from_user.id

        # Get or create user and get token
        auth_service = AuthService()
        user, token = await auth_service.authenticate_telegram_user(telegram_id)

        # Проверяем наличие активной подписки
        subscription_service = SubscriptionService()
        active_sub = await subscription_service.get_active_subscription(user.id, token.access_token)

        if not active_sub:
            text = (
                "❌ <b>Нет активной подписки</b>\n\n"
                "Промокоды можно применять только к активной подписке.\n\n"
                "Оформите подписку, чтобы использовать промокоды."
            )
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="📋 Планы подписок", callback_data="view_plans")],
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")],
                ]
            )
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
            return

        # Получаем информацию о промокоде для получения кода
        promotion_service = PromotionService()
        promotions = await promotion_service.get_available_promotions(token.access_token)
        promo = next((p for p in promotions if p.id == promo_id), None)

        if not promo:
            text = "❌ <b>Промокод не найден или больше недоступен</b>"
            kb = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="promo_menu")]]
            )
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
            return

        # Применяем промокод к подписке
        result = await subscription_service.apply_promotion_to_subscription(
            subscription_id=active_sub.id, promotion_code=promo.code, token=token.access_token
        )

        # Формируем сообщение об успехе
        old_end_date = result.old_end_date
        new_end_date = result.new_end_date
        bonus_days = result.bonus_days

        # API клиент уже возвращает datetime объекты
        old_end_str = old_end_date.strftime("%d.%m.%Y") if isinstance(old_end_date, datetime) else str(old_end_date)
        new_end_str = new_end_date.strftime("%d.%m.%Y") if isinstance(new_end_date, datetime) else str(new_end_date)

        text = (
            f"✅ <b>Промокод успешно применен!</b>\n\n"
            f"🎁 Промокод: <b>{promo.code}</b>\n"
            f"➕ Добавлено бонусных дней: <b>{bonus_days}</b>\n\n"
            f"📅 Дата окончания была: {old_end_str}\n"
            f"📅 Дата окончания теперь: {new_end_str}\n\n"
            f"{result.message}"
        )

        kb = SubscriptionKeyboards.main_menu_keyboard()
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

    except Exception as e:
        logger.error(f"Error applying promotion: {e}")
        error_msg = str(e)

        # Улучшаем сообщения об ошибках
        if "already used" in error_msg.lower() or "уже использован" in error_msg.lower():
            text = "❌ <b>Этот промокод уже был использован</b>\n\nПопробуйте другой промокод."
        elif "not found" in error_msg.lower() or "не найден" in error_msg.lower():
            text = "❌ <b>Промокод не найден</b>\n\nПроверьте правильность кода."
        elif "not active" in error_msg.lower() or "не активен" in error_msg.lower():
            text = "❌ <b>Промокод не активен</b>\n\nЭтот промокод больше не действует."
        elif "expired" in error_msg.lower() or "истек" in error_msg.lower():
            text = "❌ <b>Промокод истек</b>\n\nСрок действия промокода закончился."
        elif "only be applied to active" in error_msg.lower() or "активной подписке" in error_msg.lower():
            text = "❌ <b>Промокод можно применить только к активной подписке</b>"
        else:
            text = f"❌ <b>Ошибка при применении промокода:</b>\n{error_msg}"

        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="promo_menu")]])

        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
