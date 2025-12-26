"""
Payment handlers for bot
"""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import PaymentKeyboards, SubscriptionKeyboards
from bot.services.auth_service import AuthService
from bot.services.payment_service import PaymentService
from bot.states.formatters import Formatters

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "payment_menu")
@router.message(F.text.contains("💰") | F.text == "Платежи")
async def payment_menu_handler(item: Message | CallbackQuery, state: FSMContext):
    """Показать все платежи пользователя"""
    # Отвечаем на callback query сразу
    if isinstance(item, CallbackQuery):
        await item.answer("⏳ Загрузка платежей...")
    else:
        # Для сообщений сразу показываем платежи
        pass

    try:
        telegram_id = item.from_user.id

        # Get or create user and get token
        auth_service = AuthService()
        user, token = await auth_service.authenticate_telegram_user(telegram_id)

        if not user or not token:
            raise Exception("Failed to authenticate user")

        payment_service = PaymentService()
        # Получаем все платежи без фильтрации
        all_payments = await payment_service.get_user_payments(user.id, token.access_token)

        if not all_payments:
            text = "❌ Нет платежей"
            kb = PaymentKeyboards.back_to_menu_keyboard()
        else:
            text = Formatters.format_payments_list(all_payments, "Все платежи")
            kb = PaymentKeyboards.back_to_menu_keyboard()

        if isinstance(item, CallbackQuery):
            await item.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        else:
            await item.answer(text, parse_mode="HTML", reply_markup=kb)

        await state.clear()

    except Exception as e:
        logger.error(f"Error showing payments: {e}", exc_info=True)
        error_msg = "❌ Ошибка при загрузке платежей"
        try:
            from bot.keyboards.inline import SubscriptionKeyboards

            if isinstance(item, CallbackQuery):
                try:
                    await item.message.edit_text(error_msg, reply_markup=SubscriptionKeyboards.main_menu_keyboard())
                except:
                    await item.message.answer(error_msg, reply_markup=SubscriptionKeyboards.main_menu_keyboard())
            else:
                await item.answer(error_msg, reply_markup=SubscriptionKeyboards.main_menu_keyboard())
        except:
            if isinstance(item, CallbackQuery):
                await item.message.answer(error_msg)
            else:
                await item.answer(error_msg)


@router.callback_query(F.data == "change_payment_method")
async def change_payment_method_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик смены карты для автосписаний"""
    await callback.answer("⏳ Создание платежа для смены карты...")

    try:
        telegram_id = callback.from_user.id

        # Get or create user and get token
        auth_service = AuthService()
        user, token = await auth_service.authenticate_telegram_user(telegram_id)

        if not user or not token:
            raise Exception("Failed to authenticate user")

        payment_service = PaymentService()
        return_url = "https://t.me/subscription_demo_billing_bot"

        # Вызываем API для создания платежа на смену карты
        result = await payment_service.change_payment_method(
            user_id=user.id, token=token.access_token, return_url=return_url, amount=1.0
        )

        # Формируем сообщение с ссылкой на оплату
        if result and hasattr(result, "confirmation_url") and result.confirmation_url:
            text = (
                "💳 <b>Смена карты для автосписаний</b>\n\n"
                "Для привязки новой карты необходимо оплатить 1 рубль.\n"
                "После успешной оплаты новая карта будет использоваться для автосписаний.\n\n"
                f"Перейдите по ссылке для оплаты:\n{result.confirmation_url}"
            )
        else:
            message = result.message if hasattr(result, "message") else "Платеж создан. Ожидайте дальнейших инструкций."
            text = f"💳 <b>Смена карты</b>\n\n{message}"

        kb = PaymentKeyboards.back_to_menu_keyboard()
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await state.clear()

    except Exception as e:
        logger.error(f"Error changing payment method: {e}", exc_info=True)
        error_msg = f"❌ Ошибка при создании платежа для смены карты: {str(e)}"
        try:
            await callback.message.edit_text(error_msg, reply_markup=SubscriptionKeyboards.main_menu_keyboard())
        except:
            await callback.message.answer(error_msg, reply_markup=SubscriptionKeyboards.main_menu_keyboard())
        await state.clear()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_from_payments(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню из платежей"""

    await callback.answer()
    await state.clear()

    try:
        text = "🏠 <b>Главное меню</b>\n\nВыберите действие:"
        await callback.message.edit_text(
            text=text, parse_mode="HTML", reply_markup=SubscriptionKeyboards.main_menu_keyboard()
        )
    except Exception as e:
        logger.warning(f"Could not edit message, sending new: {e}")
        text = "🏠 <b>Главное меню</b>\n\nВыберите действие:"
        await callback.message.answer(
            text=text, parse_mode="HTML", reply_markup=SubscriptionKeyboards.main_menu_keyboard()
        )
