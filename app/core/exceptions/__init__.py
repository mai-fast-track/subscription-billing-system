class ApplicationException(Exception):
    entity_name: str = "Entity"
    message_template: str = "{entity_name}: {identifier}"

    def __init__(self, identifier: int | str | None = None):
        self.identifier = identifier
        message = self.message_template.format(entity_name=self.entity_name, identifier=identifier)
        super().__init__(message)


class UserNotFound(ApplicationException):
    entity_name = "User"
    message_template = "User not found: {identifier}"


class UserAlreadyExists(ApplicationException):
    entity_name = "User"
    message_template = "User already exists: {identifier}"


class SubscriptionNotFound(ApplicationException):
    entity_name = "Subscription"
    message_template = "Subscription not found: {identifier}"


class PaymentNotFound(ApplicationException):
    entity_name = "Payment"
    message_template = "Payment not found: {identifier}"


class RefundNotFound(ApplicationException):
    entity_name = "Refund"
    message_template = "Refund not found: {identifier}"


class SubscriptionPlanNotFound(ApplicationException):
    entity_name = "SubscriptionPlan"
    message_template = "SubscriptionPlan not found: {identifier}"


class SubscriptionAlreadyActive(ApplicationException):
    """Подписка уже активна"""

    def __init__(self, user_id: int, subscription_id: int):
        self.user_id = user_id
        self.subscription_id = subscription_id
        super().__init__(f"User {user_id} already has active subscription {subscription_id}")


class PromotionNotFound(ApplicationException):
    entity_name = "Promotion"
    message_template = "Promotion not found: {identifier}"


class InvalidSubscriptionStatus(ApplicationException):
    """Неверный статус подписки"""

    def __init__(self, status: str, valid_statuses: list):
        self.status = status
        self.valid_statuses = valid_statuses
        super().__init__(f"Invalid status '{status}'. Valid: {valid_statuses}")


class TrialPeriodNotAvailable(ApplicationException):
    """Промопериод недоступен"""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Trial period not available: {reason}")
