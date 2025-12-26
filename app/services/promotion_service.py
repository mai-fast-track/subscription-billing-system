"""
Promotion service - бизнес-логика для работы с промокодами
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy.exc import IntegrityError

from app.core.enums import PromotionType, SubscriptionStatus
from app.core.logger import logger
from app.models.promotion import Promotion
from app.schemas.promotion import PromotionCreate, PromotionUpdate
from app.services.base_service import BaseService


class PromotionService(BaseService):
    """Сервис для работы с промокодами"""

    async def validate_and_apply_promotion(
        self, code: str, user_id: Optional[int] = None
    ) -> tuple[Optional[Promotion], Optional[str]]:
        """
        Валидирует промокод и возвращает его, если валиден

        Args:
            code: Код промокода
            user_id: ID пользователя (для проверки повторного использования)

        Returns:
            Tuple[Promotion, error_message]: (promotion, None) если валиден, (None, error) если нет
        """
        try:
            promotion = await self.uow.promotions.get_by_code(code)

            if not promotion:
                return None, f"Promotion code '{code}' not found"

            # Проверка активности
            if not promotion.is_active:
                return None, "Promotion is not active"

            # Проверка дат
            now = datetime.now(timezone.utc)
            if promotion.valid_from > now:
                return None, "Promotion is not yet valid"

            if promotion.valid_until and promotion.valid_until < now:
                return None, "Promotion has expired"

            # Проверка лимита использований (глобальный)
            if promotion.max_uses is not None and promotion.current_uses >= promotion.max_uses:
                return None, "Promotion has reached maximum usage limit"

            # Промокоды поддерживают только тип bonus_days
            if promotion.type != PromotionType.bonus_days:
                return None, f"Promotion type '{promotion.type}' is not supported. Only 'bonus_days' is allowed."

            # Проверка назначения промокода пользователю
            if promotion.assigned_user_id is not None:
                if not user_id:
                    return None, "This promotion is assigned to a specific user. User ID is required."
                if promotion.assigned_user_id != user_id:
                    return None, "This promotion is not available for you"

            # Проверка, использовал ли пользователь этот промокод ранее
            if user_id:
                has_used = await self.uow.user_promotion_usage.has_user_used_promotion(
                    user_id=user_id, promotion_id=promotion.id
                )
                if has_used:
                    return None, "You have already used this promotion code"

            return promotion, None

        except Exception as e:
            return None, f"Error validating promotion: {str(e)}"

    async def increment_usage(self, promotion_id: int) -> bool:
        """
        Увеличивает счетчик использований промокода

        Args:
            promotion_id: ID промокода

        Returns:
            bool: True если успешно

        Raises:
            ValueError: Если промокод достиг лимита использований
        """
        try:
            await self.uow.promotions.increment_usage(promotion_id)
            return True
        except ValueError:
            raise
        except Exception:
            return False

    @staticmethod
    def calculate_bonus_days(original_days: int, bonus_value: int = 0) -> int:
        """
        Вычисляет дополнительные дни на основе промокода

        Args:
            original_days: Исходное количество дней
            bonus_value: Количество бонусных дней

        Returns:
            int: количество дней с учетом бонусных дней
        """
        return original_days + bonus_value

    async def apply_promotion_to_active_subscription(self, subscription_id: int, promotion_code: str) -> dict[str, Any]:
        """
        Применить промокод к активной подписке.
        Продлевает end_date на количество бонусных дней.

        Args:
            subscription_id: ID активной подписки
            promotion_code: Код промокода

        Returns:
            Dict с результатом применения

        Raises:
            ValueError: Если промокод невалиден или подписка неактивна
            IntegrityError: Если промокод уже использован (race condition)
        """
        logger.info(f"Attempting to apply promotion code '{promotion_code}' to subscription {subscription_id}")

        # 1. Получаем подписку с блокировкой FOR UPDATE для предотвращения race conditions
        subscription = await self.uow.subscriptions.get_for_update_or_raise(subscription_id)

        # 2. Проверяем, что подписка активна
        if subscription.status != SubscriptionStatus.active.value:
            logger.warning(
                f"Failed to apply promotion: subscription {subscription_id} "
                f"is not active (status: {subscription.status})"
            )
            raise ValueError("Promotion can only be applied to active subscriptions")

        # 3. Валидируем промокод
        promotion, error = await self.validate_and_apply_promotion(
            code=promotion_code,
            user_id=subscription.user_id,
        )

        if error:
            logger.warning(f"Failed to apply promotion '{promotion_code}' to subscription {subscription_id}: {error}")
            raise ValueError(f"Invalid promotion code: {error}")

        # 4. Продлеваем подписку (добавляем бонусные дни к end_date)
        bonus_days = promotion.value or 0
        if bonus_days <= 0:
            raise ValueError("Promotion value must be greater than 0")

        old_end_date = subscription.end_date
        subscription.end_date = subscription.end_date + timedelta(days=bonus_days)
        subscription.promotion_id = promotion.id  # Связываем с промокодом
        subscription.updated_at = datetime.now(timezone.utc)

        await self.uow.subscriptions.update(subscription)

        # 5. Записываем использование промокода (с обработкой IntegrityError)
        try:
            await self.uow.user_promotion_usage.create_usage(
                user_id=subscription.user_id,
                promotion_id=promotion.id,
                subscription_id=subscription.id,
            )
        except IntegrityError:
            # Промокод уже использован (race condition)
            logger.warning(
                f"Promotion '{promotion_code}' (id={promotion.id}) was already used "
                f"by user {subscription.user_id} (race condition detected)"
            )
            await self.uow.rollback()
            raise ValueError("You have already used this promotion code")

        # 6. Увеличиваем глобальный счетчик использований (с проверкой лимита)
        try:
            await self.uow.promotions.increment_usage(promotion.id)
        except ValueError as e:
            # Промокод достиг лимита использований
            logger.warning(f"Promotion '{promotion_code}' (id={promotion.id}) reached usage limit")
            await self.uow.rollback()
            raise ValueError(str(e))

        logger.info(
            f"Promotion '{promotion_code}' (id={promotion.id}) successfully applied "
            f"to subscription {subscription_id} for user {subscription.user_id}. "
            f"Subscription extended from {old_end_date} to {subscription.end_date} "
            f"(+{bonus_days} days)"
        )

        return {
            "success": True,
            "message": f"Promotion applied successfully. Subscription extended by {bonus_days} days",
            "subscription_id": subscription.id,
            "old_end_date": old_end_date,
            "new_end_date": subscription.end_date,
            "bonus_days": bonus_days,
        }

    async def get_available_promotions_for_user(self, user_id: int) -> list[Promotion]:
        """
        Получить список доступных промокодов для пользователя.

        Включает:
        - Общие промокоды (assigned_user_id = None)
        - Личные промокоды пользователя (assigned_user_id = user_id)

        Исключает:
        - Промокоды, которые пользователь уже использовал
        - Неактивные промокоды
        - Промокоды с истекшим сроком действия
        - Промокоды, достигшие лимита использований

        Args:
            user_id: ID пользователя

        Returns:
            List доступных промокодов
        """
        # Получаем все доступные промокоды из репозитория
        # Фильтрация по использованию уже выполняется в SQL запросе (LEFT JOIN)
        promotions = await self.uow.promotions.get_available_promotions_for_user(user_id)

        return list(promotions)

    async def get_all_promotions(self, skip: int = 0, limit: int = 100) -> list[Promotion]:
        """
        Получить все промокоды с пагинацией

        Args:
            skip: Количество записей для пропуска
            limit: Максимальное количество записей

        Returns:
            List промокодов
        """
        promotions = await self.uow.promotions.get_all(skip=skip, limit=limit)
        return list(promotions)

    async def get_promotion_by_id(self, promotion_id: int) -> Optional[Promotion]:
        """
        Получить промокод по ID

        Args:
            promotion_id: ID промокода

        Returns:
            Promotion или None если не найден
        """
        return await self.uow.promotions.get_by_id(promotion_id)

    async def create_promotion(self, promotion_data: PromotionCreate) -> Promotion:
        """
        Создать новый промокод

        Args:
            promotion_data: Данные для создания промокода

        Returns:
            Созданный промокод

        Raises:
            ValueError: Если код уже существует или данные невалидны
        """
        # Проверяем, что тип = bonus_days
        if promotion_data.type != PromotionType.bonus_days:
            raise ValueError("Only 'bonus_days' promotion type is supported")

        # Нормализуем код (uppercase)
        code_upper = promotion_data.code.upper()

        # Проверяем, что код уникален
        existing = await self.uow.promotions.get_by_code(code_upper)
        if existing:
            raise ValueError(f"Promotion code '{code_upper}' already exists")

        # Создаем промокод
        promotion = Promotion(
            code=code_upper,
            name=promotion_data.name,
            description=promotion_data.description,
            type=promotion_data.type.value,
            value=promotion_data.value,
            valid_from=promotion_data.valid_from,
            valid_until=promotion_data.valid_until,
            is_active=True,  # По умолчанию активен
            max_uses=promotion_data.max_uses,
            assigned_user_id=promotion_data.assigned_user_id,
        )

        created = await self.uow.promotions.create(promotion)
        logger.info(f"Created promotion {created.id} with code '{code_upper}'")

        # Отправляем уведомление пользователю, если промокод персональный
        if created.assigned_user_id:
            await self._send_promotion_notification(created)

        return created

    async def update_promotion(self, promotion_id: int, promotion_update: PromotionUpdate) -> Promotion:
        """
        Обновить промокод

        Args:
            promotion_id: ID промокода
            promotion_update: Данные для обновления

        Returns:
            Обновленный промокод

        Raises:
            ValueError: Если промокод не найден
        """
        promotion = await self.uow.promotions.get_by_id_or_raise(promotion_id)

        # Обновляем только переданные поля
        if promotion_update.name is not None:
            promotion.name = promotion_update.name
        if promotion_update.description is not None:
            promotion.description = promotion_update.description
        if promotion_update.valid_until is not None:
            # Проверяем, что valid_until позже valid_from
            if promotion_update.valid_until <= promotion.valid_from:
                raise ValueError("valid_until должна быть позже valid_from")
            promotion.valid_until = promotion_update.valid_until
        if promotion_update.is_active is not None:
            promotion.is_active = promotion_update.is_active
        if promotion_update.max_uses is not None:
            # Проверяем, что max_uses не меньше текущего количества использований
            if promotion_update.max_uses < promotion.current_uses:
                raise ValueError(
                    f"max_uses ({promotion_update.max_uses}) cannot be less than current_uses ({promotion.current_uses})"
                )
            promotion.max_uses = promotion_update.max_uses

        promotion.updated_at = datetime.now(timezone.utc)
        updated = await self.uow.promotions.update(promotion)
        logger.info(f"Updated promotion {updated.id} with code '{updated.code}'")
        return updated

    async def delete_promotion(self, promotion_id: int) -> None:
        """
        Удалить промокод

        Args:
            promotion_id: ID промокода

        Raises:
            ValueError: Если промокод не найден или используется
        """
        promotion = await self.uow.promotions.get_by_id_or_raise(promotion_id)

        # Проверяем, используется ли промокод
        usage_count = await self.uow.user_promotion_usage.count(promotion_id=promotion_id)
        if usage_count > 0:
            raise ValueError(
                f"Cannot delete promotion {promotion_id}: it has been used {usage_count} time(s). "
                "Deactivate it instead by setting is_active=False"
            )

        await self.uow.promotions.delete(promotion)
        logger.info(f"Deleted promotion {promotion_id} with code '{promotion.code}'")

    def _format_promotion_notification(self, promotion: Promotion) -> str:
        """
        Форматировать сообщение о новом промокоде для отправки пользователю

        Args:
            promotion: Промокод

        Returns:
            Отформатированное HTML сообщение
        """
        # Форматирование даты окончания
        valid_until_str = "Без ограничений"
        if promotion.valid_until:
            valid_until_str = promotion.valid_until.strftime("%d.%m.%Y")

        message = f"""🎁 <b>У вас новый промокод!</b>

📝 <b>{promotion.name}</b>
🎫 Код: <code>{promotion.code}</code>
➕ Бонусных дней: <b>{promotion.value}</b>"""

        if promotion.description:
            message += f"\n\n{promotion.description}"

        message += f"\n\n📅 Действует до: {valid_until_str}"

        if promotion.max_uses:
            message += f"\n🔢 Лимит использований: {promotion.max_uses}"

        message += '\n\nИспользуйте промокод в разделе "🎁 Промокоды" для продления подписки!'

        return message

    async def _send_promotion_notification(self, promotion: Promotion) -> None:
        """
        Отправить уведомление пользователю о новом персональном промокоде

        Args:
            promotion: Созданный промокод
        """
        if not promotion.assigned_user_id:
            return  # Не отправляем для общих промокодов

        try:
            from app.tasks.notification import send_notification

            # Формируем сообщение
            message = self._format_promotion_notification(promotion)

            # Отправляем асинхронно через Celery
            send_notification.delay(
                user_id=promotion.assigned_user_id,
                message=message,
                notification_type="promotion",
            )

            logger.info(
                f"Promotion notification queued for user {promotion.assigned_user_id} "
                f"(promotion_id={promotion.id}, code={promotion.code})"
            )
        except Exception as e:
            # Не прерываем создание промокода при ошибке уведомления
            logger.error(
                f"Failed to queue promotion notification for user {promotion.assigned_user_id}: {str(e)}",
                exc_info=True,
            )
