import enum


class UserRole(str, enum.Enum):
    client = "client"
    admin = "admin"


class SubscriptionStatus(str, enum.Enum):
    active = "active"
    cancelled = "cancelled"
    cancelled_waiting = "cancelled_waiting"  # Ожидает отмены в конце дня после неудачных попыток автосписания
    expired = "expired"
    pending_payment = "pending_payment"


class PromotionType(str, enum.Enum):
    bonus_days = "bonus_days"


class SubscriptionPlans(str, enum.Enum):
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class PaymentStatus(str, enum.Enum):
    """Статусы платежей в системе"""

    pending = "pending"
    waiting_for_capture = "waiting_for_capture"  # двухстадийные
    succeeded = "succeeded"
    cancelled = "cancelled"
    failed = "failed"
