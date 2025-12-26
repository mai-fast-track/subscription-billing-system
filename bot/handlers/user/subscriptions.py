import logging

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.common.texts.subscriptions import PLANS_NOT_FOUND
from bot.keyboards.inline import PaymentKeyboards, SubscriptionKeyboards
from bot.services.auth_service import AuthService
from bot.services.subscription_service import SubscriptionService
from bot.states.formatters import Formatters
from bot.states.user_states import SubscriptionStates

logger = logging.getLogger(__name__)
router = Router()


# FSM — показ планов
@router.callback_query(F.data == "view_plans")
@router.message(F.text == "Купить подписку")
async def start_subscription_view(message_or_callback: Message | CallbackQuery, state: FSMContext):
    """Старт FSM — выбор плана"""
    # Отвечаем на callback query сразу, чтобы избежать timeout
    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.answer()

    try:
        subscription_service = SubscriptionService()
        plans = await subscription_service.get_all_plans()
        if not plans:
            if isinstance(message_or_callback, CallbackQuery):
                await message_or_callback.message.edit_text(PLANS_NOT_FOUND)
            else:
                await message_or_callback.answer(PLANS_NOT_FOUND)
            return

        text = "💳 Доступные планы подписок:\n\n" + "\n".join(
            Formatters.format_subscription_plan(plan) for plan in plans
        )

        kb = SubscriptionKeyboards.subscription_plans_keyboard(plans)

        if isinstance(message_or_callback, CallbackQuery):
            await message_or_callback.message.edit_text(text, reply_markup=kb)
        else:
            await message_or_callback.answer(text, reply_markup=kb)

        await state.set_state(SubscriptionStates.choosing_plan)  # Вход в FSM
    except Exception as e:
        logger.error(f"Error showing plans: {e}")
        error_msg = "❌ Ошибка при загрузке планов"
        if isinstance(message_or_callback, CallbackQuery):
            try:
                await message_or_callback.message.edit_text(error_msg)
            except:
                await message_or_callback.message.answer(error_msg)
        else:
            await message_or_callback.answer(error_msg)


# FSM: выбор плана
@router.callback_query(StateFilter(SubscriptionStates.choosing_plan), F.data.startswith("subscribe_"))
async def process_plan_choice(callback: CallbackQuery, state: FSMContext):
    """FSM: Выбор плана → переход к подтверждению с проверкой промопериода"""
    # Отвечаем на callback query сразу
    await callback.answer()

    try:
        plan_id = int(callback.data.split("_")[-1])
        telegram_id = callback.from_user.id

        subscription_service = SubscriptionService()
        plan = await subscription_service.get_plan_by_id(plan_id)
        if not plan:
            await callback.message.edit_text("❌ План не найден")
            return

        # Get or create user and get token for checking trial eligibility
        auth_service = AuthService()
        user, token = await auth_service.authenticate_telegram_user(telegram_id)

        # Check trial eligibility
        trial_eligible = False
        try:
            eligibility = await subscription_service.check_trial_eligibility(user.id, token.access_token)
            trial_eligible = eligibility.is_eligible if eligibility else False
        except Exception as e:
            logger.warning(f"Failed to check trial eligibility for user {user.id}: {e}")
            # If check fails, assume trial is not available
            trial_eligible = False

        await state.update_data(plan_id=plan_id, user_id=user.id, token=token.access_token)  # ✅ Сохраняем в FSM

        text = f"{Formatters.format_subscription_plan(plan)}\n\n💰 Итого: {plan.price} ₽"
        if trial_eligible:
            text += "\n\n🎁 Доступен промопериод для новых пользователей!"

        kb = SubscriptionKeyboards.confirm_subscription_keyboard(plan_id, trial_eligible=trial_eligible)

        await callback.message.edit_text(text, reply_markup=kb)
        await state.set_state(SubscriptionStates.confirming_subscription)  # ✅ Следующий шаг FSM
    except Exception as e:
        logger.error(f"Error processing plan choice: {e}")
        try:
            await callback.message.edit_text("❌ Ошибка при выборе плана")
        except:
            pass


# FSM: создание промопериода
@router.callback_query(StateFilter(SubscriptionStates.confirming_subscription), F.data.startswith("create_trial_"))
async def process_trial_subscription(callback: CallbackQuery, state: FSMContext):
    """FSM: Создание промопериода"""
    # Отвечаем на callback query сразу
    await callback.answer("⏳ Активация промопериода...")

    try:
        data = await state.get_data()
        plan_id = data.get("plan_id")
        user_id = data.get("user_id")
        token = data.get("token")

        if not plan_id or not user_id or not token:
            await callback.message.edit_text("❌ Ошибка: данные не найдены")
            await state.clear()
            return

        subscription_service = SubscriptionService()

        # Проверяем активную подписку перед созданием промопериода
        active_sub = await subscription_service.get_active_subscription(user_id, token)
        if active_sub:
            text = (
                "⚠️ <b>У вас уже есть активная подписка</b>\n\n"
                "Чтобы оформить новую подписку, сначала необходимо отменить текущую.\n\n"
                'Перейдите в раздел "✅ Моя подписка" для отмены.'
            )
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Моя подписка", callback_data="my_subscription")],
                    [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")],
                ]
            )
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
            await state.clear()
            return

        # Create trial subscription
        result = await subscription_service.create_trial_subscription(
            user_id=user_id,
            plan_id=plan_id,
            token=token,
        )

        if result:
            # Format end date
            end_date_str = result.end_date.strftime("%d.%m.%Y") if hasattr(result, "end_date") else "N/A"

            text = (
                f"✅ Промопериод активирован!\n\n"
                f"🎁 Вам предоставлен пробный период до {end_date_str}.\n"
                f"💡 Платеж будет создан автоматически при окончании пробного периода."
            )
            kb = SubscriptionKeyboards.main_menu_keyboard()
            await state.clear()  # Выходим из FSM

            await callback.message.edit_text(text, reply_markup=kb)
    except Exception as e:
        logger.error(f"Error creating trial subscription: {e}")
        await state.clear()

        # Проверяем, не является ли ошибка связанной с активной подпиской
        error_str = str(e).lower()
        if "already has active" in error_str or "уже есть активная" in error_str:
            text = (
                "⚠️ <b>У вас уже есть активная подписка</b>\n\n"
                "Чтобы оформить новую подписку, сначала необходимо отменить текущую.\n\n"
                'Перейдите в раздел "✅ Моя подписка" для отмены.'
            )
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Моя подписка", callback_data="my_subscription")],
                    [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")],
                ]
            )
        else:
            text = f"❌ Ошибка при активации промопериода: {str(e)}"
            kb = SubscriptionKeyboards.main_menu_keyboard()

        try:
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except:
            try:
                await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
            except:
                pass


# FSM: подтверждение (обычное оформление без промопериода)
@router.callback_query(StateFilter(SubscriptionStates.confirming_subscription), F.data.startswith("confirm_subscribe_"))
async def process_subscription_confirm(callback: CallbackQuery, state: FSMContext):
    """FSM: Подтверждение → создание подписки с оплатой"""
    # Отвечаем на callback query сразу, так как операция может занять время
    await callback.answer("⏳ Оформление подписки...")

    try:
        data = await state.get_data()
        plan_id = data.get("plan_id")
        user_id = data.get("user_id")
        token = data.get("token")

        if not plan_id or not user_id or not token:
            telegram_id = callback.from_user.id
            # Get or create user and get token
            auth_service = AuthService()
            user, new_token = await auth_service.authenticate_telegram_user(telegram_id)
            user_id = user.id
            token = new_token.access_token
            await state.update_data(user_id=user_id, token=token)

        subscription_service = SubscriptionService()
        active_sub = await subscription_service.get_active_subscription(user_id, token)
        if active_sub:
            # Улучшенное сообщение с предложением отменить текущую подписку
            text = (
                "⚠️ <b>У вас уже есть активная подписка</b>\n\n"
                "Чтобы оформить новую подписку, сначала необходимо отменить текущую.\n\n"
                'Перейдите в раздел "✅ Моя подписка" для отмены.'
            )
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Моя подписка", callback_data="my_subscription")],
                    [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")],
                ]
            )
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
            await state.clear()
            return

        # Create subscription with payment (обычное оформление)
        return_url = "https://t.me/subscription_demo_billing_bot"

        result = await subscription_service.create_subscription_with_payment(
            user_id=user_id,
            plan_id=plan_id,
            return_url=return_url,
            token=token,
        )

        # Format response message
        if result:
            # Handle confirmation_url (can be None, UNSET, or string)
            from billing_core_api_client.types import UNSET

            confirmation_url = None
            if hasattr(result, "confirmation_url"):
                if result.confirmation_url is not UNSET:
                    confirmation_url = result.confirmation_url

            if confirmation_url:
                text = f"✅ Подписка создана!\n\n💳 Перейдите по ссылке для оплаты:\n{confirmation_url}"
            else:
                message = result.message if hasattr(result, "message") else "Ожидайте дальнейших инструкций."
                text = f"✅ Подписка создана!\n\n{message}"

            kb = SubscriptionKeyboards.main_menu_keyboard()
            await state.clear()  # Выходим из FSM после создания подписки

            await callback.message.edit_text(text, reply_markup=kb)
    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        await state.clear()

        # Проверяем, не является ли ошибка связанной с активной подпиской
        error_str = str(e).lower()
        if "already has active" in error_str or "уже есть активная" in error_str:
            text = (
                "⚠️ <b>У вас уже есть активная подписка</b>\n\n"
                "Чтобы оформить новую подписку, сначала необходимо отменить текущую.\n\n"
                'Перейдите в раздел "✅ Моя подписка" для отмены.'
            )
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Моя подписка", callback_data="my_subscription")],
                    [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")],
                ]
            )
        else:
            text = f"❌ Ошибка при создании подписки: {str(e)}"
            kb = SubscriptionKeyboards.main_menu_keyboard()

        try:
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except:
            try:
                await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
            except:
                pass


# FSM: после подтверждения (оплата/результат) - этот обработчик больше не нужен,
# так как мы сразу выходим из FSM после создания подписки
# Оставлен для совместимости, но не используется
@router.message(StateFilter(SubscriptionStates.subscription_confirmed))
async def after_subscription(message: Message, state: FSMContext):
    """FSM: Финальный шаг — обработка сообщений после подтверждения"""
    from bot.keyboards.inline import SubscriptionKeyboards

    await message.answer(
        "💡 Подписка уже создана. Используйте меню для управления подпиской.",
        reply_markup=SubscriptionKeyboards.main_menu_keyboard(),
    )
    await state.clear()  # ✅ Выход из FSM


# Отмена везде
@router.callback_query(F.data == "cancel_subscribe")
async def cancel_subscription_anywhere(callback: CallbackQuery, state: FSMContext):
    """Отмена на любом шаге FSM - возврат в главное меню"""
    # Отвечаем на callback query сразу
    await callback.answer("❌ Оформление отменено")

    await state.clear()
    try:
        from bot.keyboards.inline import SubscriptionKeyboards

        await callback.message.edit_text(
            "❌ Оформление подписки отменено", reply_markup=SubscriptionKeyboards.main_menu_keyboard()
        )
    except:
        from bot.keyboards.inline import SubscriptionKeyboards

        await callback.message.answer(
            "❌ Оформление подписки отменено", reply_markup=SubscriptionKeyboards.main_menu_keyboard()
        )


@router.message(F.text.contains("✅ Моя") | Command("my_subscription"))
@router.callback_query(F.data == "my_subscription")
async def show_my_subscription(item: Message | CallbackQuery):
    # Отвечаем на callback query сразу
    if isinstance(item, CallbackQuery):
        await item.answer()

    try:
        telegram_id = item.from_user.id

        # Get or create user and get token
        auth_service = AuthService()
        user, token = await auth_service.authenticate_telegram_user(telegram_id)

        subscription_service = SubscriptionService()
        active_sub = await subscription_service.get_active_subscription(user.id, token.access_token)

        text: str
        if not active_sub:
            text = "❌ Нет активной подписки"
            kb = PaymentKeyboards.back_to_menu_keyboard()
        else:
            # Plan is already included in SubscriptionDetailResponse
            text = Formatters.format_active_subscription(active_sub, plan=active_sub.plan)

            # Проверяем статус подписки - не показываем кнопку отмены для уже отмененных
            subscription_status = getattr(active_sub, "status", "active")
            # Преобразуем статус в строку, если это enum
            if hasattr(subscription_status, "value"):
                subscription_status = subscription_status.value
            subscription_status = str(subscription_status).lower()
            if subscription_status in ["cancelled", "cancelled_waiting"]:
                # Для отмененных подписок показываем только кнопку назад
                kb = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")],
                    ]
                )
            else:
                # Для активных подписок показываем кнопки отмены и применения промокода
                kb = SubscriptionKeyboards.active_subscription_keyboard(active_sub.id)

        if isinstance(item, CallbackQuery):
            await item.message.edit_text(text, reply_markup=kb)
        else:
            await item.answer(text, reply_markup=kb)
    except Exception as e:
        logger.error(f"Error showing subscription: {e}")
        error_msg = "❌ Ошибка при загрузке подписки"
        if isinstance(item, CallbackQuery):
            try:
                await item.message.edit_text(error_msg)
            except:
                pass
        else:
            await item.answer(error_msg)


@router.callback_query(
    F.data.startswith("cancel_sub_") & ~F.data.contains("_no_refund_") & ~F.data.contains("_with_refund_")
)
async def show_cancellation_options(callback: CallbackQuery):
    """Показать варианты отмены подписки"""
    await callback.answer()

    try:
        telegram_id = callback.from_user.id
        sub_id = int(callback.data.split("_")[-1])

        # Get or create user and get token
        auth_service = AuthService()
        user, token = await auth_service.authenticate_telegram_user(telegram_id)

        subscription_service = SubscriptionService()
        subscription = await subscription_service.get_subscription_by_id(sub_id, token.access_token)
        if subscription and subscription.user_id == user.id:
            # Проверяем, не отменена ли уже подписка
            subscription_status = getattr(subscription, "status", "active")
            if subscription_status in ["cancelled", "cancelled_waiting"]:
                text = (
                    "ℹ️ <b>Подписка уже отменена</b>\n\n"
                    "Эта подписка была ранее отменена. "
                    "Вы можете оформить новую подписку в любое время."
                )
                kb = SubscriptionKeyboards.main_menu_keyboard()
                await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
                return

            # Показываем выбор типа отмены
            text = (
                "❌ <b>Отмена подписки</b>\n\n"
                "Выберите тип отмены:\n\n"
                "⏸️ <b>Отменить (активна до конца периода)</b>\n"
                "Подписка останется активной до конца оплаченного периода.\n"
                "Возврат средств не выполняется.\n\n"
                "❌ <b>Отменить с возвратом</b>\n"
                "Подписка отменяется немедленно.\n"
                "Выполняется возврат за неиспользованную часть.\n"
                "Доступ прекращается сразу."
            )
            kb = SubscriptionKeyboards.choose_cancellation_type_keyboard(sub_id)
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        else:
            await callback.message.edit_text("❌ Подписка не найдена")
    except Exception as e:
        logger.error(f"Error showing cancellation options: {e}")
        await callback.message.edit_text("❌ Ошибка при загрузке опций отмены")


@router.callback_query(F.data.startswith("cancel_sub_no_refund_"))
async def cancel_subscription_no_refund(callback: CallbackQuery):
    """Отмена подписки без возврата"""
    await callback.answer("⏳ Отмена подписки...")

    try:
        telegram_id = callback.from_user.id
        sub_id = int(callback.data.split("_")[-1])

        # Get or create user and get token
        auth_service = AuthService()
        user, token = await auth_service.authenticate_telegram_user(telegram_id)

        subscription_service = SubscriptionService()
        subscription = await subscription_service.get_subscription_by_id(sub_id, token.access_token)
        if subscription and subscription.user_id == user.id:
            # Проверяем, не отменена ли уже подписка
            subscription_status = getattr(subscription, "status", "active")
            if subscription_status in ["cancelled", "cancelled_waiting"]:
                text = (
                    "ℹ️ <b>Подписка уже отменена</b>\n\n"
                    "Эта подписка была ранее отменена. "
                    "Вы можете оформить новую подписку в любое время."
                )
                kb = SubscriptionKeyboards.main_menu_keyboard()
                await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
                return

            # Отменяем подписку без возврата
            cancelled_subscription = await subscription_service.cancel_subscription(
                sub_id, token.access_token, with_refund=False
            )

            # Формируем сообщение для отмены без возврата
            end_date = cancelled_subscription.end_date
            if isinstance(end_date, str):
                from dateutil import parser

                end_date = parser.parse(end_date)

            end_date_str = end_date.strftime("%d.%m.%Y") if hasattr(end_date, "strftime") else str(end_date)

            text = (
                "❌ <b>Подписка отменена</b>\n\n"
                f"✅ Ваша подписка остается активной до <b>{end_date_str}</b>.\n\n"
                "После этой даты подписка будет автоматически деактивирована.\n"
                "Автоплатежи отключены.\n\n"
                "💳 <b>Возврат средств:</b>\n"
                "Возврат средств не выполняется. Подписка активна до конца оплаченного периода.\n\n"
                "Вы можете оформить новую подписку в любое время."
            )

            kb = SubscriptionKeyboards.main_menu_keyboard()
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        else:
            await callback.message.edit_text("❌ Подписка не найдена")
            return
    except Exception as e:
        logger.error(f"Error canceling subscription: {e}")
        error_message = "❌ Ошибка при отмене подписки"

        # Проверяем, не связана ли ошибка с тем, что подписка уже отменена
        error_str = str(e).lower()
        if "уже отменена" in error_str or "already cancelled" in error_str:
            error_message = (
                "ℹ️ <b>Подписка уже отменена</b>\n\n"
                "Эта подписка была ранее отменена. "
                "Вы можете оформить новую подписку в любое время."
            )

        try:
            await callback.message.edit_text(error_message, parse_mode="HTML")
        except:
            pass


@router.callback_query(F.data.startswith("cancel_sub_with_refund_"))
async def cancel_subscription_with_refund(callback: CallbackQuery):
    """Отмена подписки с возвратом"""
    await callback.answer("⏳ Отмена подписки с возвратом...")

    try:
        telegram_id = callback.from_user.id
        sub_id = int(callback.data.split("_")[-1])

        # Get or create user and get token
        auth_service = AuthService()
        user, token = await auth_service.authenticate_telegram_user(telegram_id)

        subscription_service = SubscriptionService()
        subscription = await subscription_service.get_subscription_by_id(sub_id, token.access_token)
        if subscription and subscription.user_id == user.id:
            # Проверяем, не отменена ли уже подписка
            subscription_status = getattr(subscription, "status", "active")
            if subscription_status in ["cancelled", "cancelled_waiting"]:
                text = (
                    "ℹ️ <b>Подписка уже отменена</b>\n\n"
                    "Эта подписка была ранее отменена. "
                    "Вы можете оформить новую подписку в любое время."
                )
                kb = SubscriptionKeyboards.main_menu_keyboard()
                await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
                return

            # Отменяем подписку с возвратом (возврат выполняется синхронно)
            try:
                await subscription_service.cancel_subscription(sub_id, token.access_token, with_refund=True)
            except RuntimeError as e:
                # Ошибка при создании возврата
                error_str = str(e).lower()
                if "не удалось создать возврат" in error_str or "возврат" in error_str:
                    text = (
                        "⚠️ <b>Подписка отменена, но возврат не выполнен</b>\n\n"
                        f"{str(e)}\n\n"
                        "Подписка была отменена, но возникла проблема при создании возврата средств. "
                        "Обратитесь в поддержку для решения вопроса о возврате."
                    )
                    kb = SubscriptionKeyboards.main_menu_keyboard()
                    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
                    return
                raise

            # Формируем сообщение для отмены с возвратом
            text = (
                "❌ <b>Подписка отменена с возвратом</b>\n\n"
                "Ваша подписка была успешно отменена.\n"
                "Доступ прекращен немедленно.\n\n"
                "💳 <b>Возврат средств:</b>\n"
                "Если вы оплатили подписку менее 14 дней назад, "
                "будет выполнен полный возврат средств.\n"
                "Если прошло более 14 дней, возврат будет пропорциональным "
                "неиспользованному периоду.\n\n"
                "Возврат средств поступит на ваш счет в течение нескольких рабочих дней "
                "(срок зависит от вашего банка, обычно 5-14 дней).\n\n"
                "Вы можете оформить новую подписку в любое время."
            )

            kb = SubscriptionKeyboards.main_menu_keyboard()
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        else:
            await callback.message.edit_text("❌ Подписка не найдена")
            return
    except Exception as e:
        logger.error(f"Error canceling subscription with refund: {e}")
        error_message = "❌ Ошибка при отмене подписки с возвратом"

        # Проверяем, не связана ли ошибка с тем, что подписка уже отменена
        error_str = str(e).lower()
        if "уже отменена" in error_str or "already cancelled" in error_str:
            error_message = (
                "ℹ️ <b>Подписка уже отменена</b>\n\n"
                "Эта подписка была ранее отменена. "
                "Вы можете оформить новую подписку в любое время."
            )

        try:
            await callback.message.edit_text(error_message, parse_mode="HTML")
        except:
            pass


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_handler(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню из любого состояния"""
    # Отвечаем на callback query сразу
    await callback.answer()

    # Очищаем состояние
    await state.clear()

    try:
        text = "🏠 <b>Главное меню</b>\n\nВыберите действие:"
        await callback.message.edit_text(
            text=text, parse_mode="HTML", reply_markup=SubscriptionKeyboards.main_menu_keyboard()
        )
    except Exception as e:
        # Если не удалось отредактировать, отправляем новое сообщение
        logger.warning(f"Could not edit message, sending new: {e}")
        text = "🏠 <b>Главное меню</b>\n\nВыберите действие:"
        await callback.message.answer(
            text=text, parse_mode="HTML", reply_markup=SubscriptionKeyboards.main_menu_keyboard()
        )
