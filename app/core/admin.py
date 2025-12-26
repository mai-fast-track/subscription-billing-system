"""
SQLAdmin configuration for database administration
"""

from typing import Any

from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.core.config import settings
from app.core.database import db_manager
from app.models import Payment, Promotion, Subscription, SubscriptionPlan, User


def get_all_model_columns(model_class: Any) -> list[Any]:
    """
    Автоматически получает все колонки из SQLAlchemy модели.

    Эта функция извлекает все колонки из модели и возвращает их в виде списка,
    который можно использовать для column_list и column_details_list в SQLAdmin.
    При добавлении новых полей в модель они автоматически появятся в админке.

    Args:
        model_class: Класс SQLAlchemy модели

    Returns:
        Список всех колонок модели для использования в SQLAdmin
    """
    columns = []
    for column_name in model_class.__table__.columns.keys():
        columns.append(getattr(model_class, column_name))
    return columns


class AdminAuth(AuthenticationBackend):
    """
    Простая аутентификация для админки.
    В продакшене рекомендуется использовать более безопасный метод.
    """

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        # Простая проверка (в продакшене использовать хеширование паролей)
        admin_username = settings.ADMIN_USERNAME
        admin_password = settings.ADMIN_PASSWORD

        if username == admin_username and password == admin_password:
            request.session.update({"authenticated": True})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return request.session.get("authenticated", False)


# Создаем экземпляр аутентификации
authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)


class UserAdmin(ModelView, model=User):
    """Админка для пользователей"""

    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"

    # Автоматически получаем все колонки для списка и деталей
    column_list = get_all_model_columns(User)
    column_details_list = get_all_model_columns(User)
    column_searchable_list = [User.telegram_id]
    column_sortable_list = [User.id, User.created_at, User.role]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True


class SubscriptionPlanAdmin(ModelView, model=SubscriptionPlan):
    """Админка для планов подписки"""

    name = "План подписки"
    name_plural = "Планы подписки"
    icon = "fa-solid fa-list"

    # Автоматически получаем все колонки для списка и деталей
    column_list = get_all_model_columns(SubscriptionPlan)
    column_details_list = get_all_model_columns(SubscriptionPlan)
    column_searchable_list = [SubscriptionPlan.name]
    column_sortable_list = [SubscriptionPlan.id, SubscriptionPlan.price, SubscriptionPlan.duration_days]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True


class SubscriptionAdmin(ModelView, model=Subscription):
    """Админка для подписок"""

    name = "Подписка"
    name_plural = "Подписки"
    icon = "fa-solid fa-credit-card"

    # Автоматически получаем все колонки для списка и деталей
    column_list = get_all_model_columns(Subscription)
    column_details_list = get_all_model_columns(Subscription)
    column_searchable_list = [Subscription.user_id, Subscription.status]
    column_sortable_list = [Subscription.id, Subscription.start_date, Subscription.end_date, Subscription.status]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True


class PaymentAdmin(ModelView, model=Payment):
    """Админка для платежей"""

    name = "Платеж"
    name_plural = "Платежи"
    icon = "fa-solid fa-money-bill"

    # Автоматически получаем все колонки для списка и деталей
    column_list = get_all_model_columns(Payment)
    column_details_list = get_all_model_columns(Payment)
    column_searchable_list = [
        Payment.yookassa_payment_id,
        Payment.idempotency_key,
        Payment.user_id,
        Payment.status,
    ]
    column_sortable_list = [
        Payment.id,
        Payment.amount,
        Payment.status,
        Payment.created_at,
        Payment.attempt_number,
    ]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True


class PromotionAdmin(ModelView, model=Promotion):
    """Админка для промокодов"""

    name = "Промокод"
    name_plural = "Промокоды"
    icon = "fa-solid fa-ticket"

    # Автоматически получаем все колонки для списка и деталей
    column_list = get_all_model_columns(Promotion)
    column_details_list = get_all_model_columns(Promotion)
    column_searchable_list = [Promotion.code, Promotion.name]
    column_sortable_list = [
        Promotion.id,
        Promotion.is_active,
        Promotion.valid_from,
        Promotion.valid_until,
        Promotion.current_uses,
    ]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True


def create_admin(app) -> Admin:
    """
    Создать и настроить админку для приложения.

    Args:
        app: FastAPI приложение

    Returns:
        Admin: Настроенный экземпляр админки
    """
    admin = Admin(
        app=app,
        engine=db_manager.engine,
        authentication_backend=authentication_backend,
        title="Billing Core Admin",
        base_url="/admin",
    )

    # Регистрируем все модели
    admin.add_view(UserAdmin)
    admin.add_view(SubscriptionPlanAdmin)
    admin.add_view(SubscriptionAdmin)
    admin.add_view(PaymentAdmin)
    admin.add_view(PromotionAdmin)

    return admin
