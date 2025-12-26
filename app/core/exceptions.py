class UserNotFound(Exception):
    """Пользователь не найден"""

    def __init__(self, user_identifier: int | str):
        self.user_identifier = user_identifier
        super().__init__(f"User not found: {user_identifier}")


class UserAlreadyExists(Exception):
    """Пользователь уже существует"""

    def __init__(self, user_identifier: int | str):
        self.user_identifier = user_identifier
        super().__init__(f"User already exists: {user_identifier}")


class SubscriptionNotFound(Exception):
    """Подписка не найдена"""

    def __init__(self, subscription_id: int):
        self.subscription_id = subscription_id
        super().__init__(f"Subscription not found: {subscription_id}")


class SubscriptionAlreadyActive(Exception):
    """Подписка уже активна"""

    def __init__(self, user_id: int, subscription_id: int):
        self.user_id = user_id
        self.subscription_id = subscription_id
        super().__init__(f"User {user_id} already has active subscription {subscription_id}")


class InvalidSubscriptionStatus(Exception):
    """Неверный статус подписки"""

    def __init__(self, status: str, valid_statuses: list):
        self.status = status
        self.valid_statuses = valid_statuses
        super().__init__(f"Invalid status '{status}'. Valid: {valid_statuses}")


class PromotionNotFound(Exception):
    """Промокод не найден"""

    def __init__(self, promotion_identifier: int | str):
        self.promotion_identifier = promotion_identifier
        super().__init__(f"Promotion not found: {promotion_identifier}")


class PaymentNotFound(Exception):
    """Платеж не найден"""

    def __init__(self, payment_id: int):
        self.payment_id = payment_id
        super().__init__(f"Payment not found: {payment_id}")


class SubscriptionPlanNotFound(Exception):
    """План подписки не найден"""

    def __init__(self, plan_id: int):
        self.plan_id = plan_id
        super().__init__(f"Subscription plan not found: {plan_id}")
