from enum import Enum


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    CANCELLED_WAITING = "cancelled_waiting"
    EXPIRED = "expired"
    PENDING_PAYMENT = "pending_payment"

    def __str__(self) -> str:
        return str(self.value)
