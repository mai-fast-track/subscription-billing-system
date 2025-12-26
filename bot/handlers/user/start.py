import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.common.texts.start import START_MSG
from bot.keyboards.inline import MainMenuKeyboard
from bot.services.user_service import UserService

logger = logging.getLogger(__name__)
router = Router()


async def send_start(message: Message):
    """Send start message and register user"""
    username = message.from_user.first_name or "Пользователь"
    text = START_MSG.format(username=username)

    # Register user via REST API
    try:
        user_service = UserService()
        telegram_id = message.from_user.id
        user = await user_service.get_or_create_user_by_telegram_id(telegram_id)
        logger.info(f"User registered/retrieved: user_id={user.id}, telegram_id={telegram_id}")
    except Exception as e:
        logger.error(f"Failed to register user: {e}")
        # Continue anyway - user can still use bot

    await message.answer(text, reply_markup=MainMenuKeyboard.main_menu_keyboard())


@router.message(Command("start"))
async def cmd_start(message: Message):
    await send_start(message)
