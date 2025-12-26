from enum import Enum


class PaymentStatus(str, Enum):
    CANCELLED = "cancelled"
    FAILED = "failed"
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    WAITING_FOR_CAPTURE = "waiting_for_capture"

    def __str__(self) -> str:
        return str(self.value)
