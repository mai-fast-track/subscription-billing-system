"""
Telegram notification service
"""

from typing import Optional

import requests

from app.core.config import settings
from app.core.logger import logger


class TelegramNotifier:
    """Сервис для отправки уведомлений в Telegram"""

    BASE_URL = "https://api.telegram.org/bot"
    TIMEOUT = 10
    MAX_RETRIES = 3

    def __init__(self, bot_token: Optional[str] = None):
        """
        Инициализация Telegram notifier

        Args:
            bot_token: Токен бота (если None, берется из settings)
        """
        self.bot_token = bot_token or settings.BOT_TOKEN or settings.TELEGRAM_BOT_TOKEN
        if not self.bot_token:
            raise ValueError("Telegram bot token is not configured")

    def send_message(
        self, chat_id: int, message: str, parse_mode: str = "HTML", disable_web_page_preview: bool = True
    ) -> bool:
        """
        Отправить сообщение в Telegram

        Args:
            chat_id: ID чата (telegram_id пользователя)
            message: Текст сообщения
            parse_mode: Режим парсинга (HTML, Markdown, MarkdownV2)
            disable_web_page_preview: Отключить предпросмотр ссылок

        Returns:
            True если сообщение отправлено успешно, False в противном случае
        """
        url = f"{self.BASE_URL}{self.bot_token}/sendMessage"

        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        }

        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.post(url, json=payload, timeout=self.TIMEOUT)

                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        logger.debug(f"Telegram message sent successfully to chat_id={chat_id}")
                        return True
                    else:
                        error_description = result.get("description", "Unknown error")
                        logger.warning(f"Telegram API returned error for chat_id={chat_id}: {error_description}")
                        # Если ошибка критическая (например, чат не найден), не повторяем
                        if "chat not found" in error_description.lower() or "blocked" in error_description.lower():
                            return False

                elif response.status_code == 429:
                    # Rate limit - получаем время ожидания
                    retry_after = response.json().get("parameters", {}).get("retry_after", 60)
                    logger.warning(f"Telegram rate limit hit for chat_id={chat_id}, waiting {retry_after} seconds")
                    if attempt < self.MAX_RETRIES - 1:
                        import time

                        time.sleep(retry_after)
                        continue

                else:
                    logger.warning(f"Telegram API returned status {response.status_code} for chat_id={chat_id}")

            except requests.exceptions.Timeout:
                logger.warning(f"Telegram API timeout for chat_id={chat_id}, attempt {attempt + 1}/{self.MAX_RETRIES}")
                if attempt == self.MAX_RETRIES - 1:
                    logger.error(f"Failed to send Telegram message after {self.MAX_RETRIES} attempts")
                    return False

            except requests.exceptions.RequestException as e:
                logger.error(
                    f"Error sending Telegram message to chat_id={chat_id}: {str(e)}, "
                    f"attempt {attempt + 1}/{self.MAX_RETRIES}"
                )
                if attempt == self.MAX_RETRIES - 1:
                    return False

            except Exception as e:
                logger.error(f"Unexpected error sending Telegram message to chat_id={chat_id}: {str(e)}")
                return False

        return False

    def send_notification_to_user(self, telegram_id: int, message: str, parse_mode: str = "HTML") -> bool:
        """
        Отправить уведомление пользователю по telegram_id

        Args:
            telegram_id: Telegram ID пользователя (используется как chat_id)
            message: Текст сообщения
            parse_mode: Режим парсинга

        Returns:
            True если сообщение отправлено успешно
        """
        return self.send_message(chat_id=telegram_id, message=message, parse_mode=parse_mode)


telegram_notifier = TelegramNotifier()
