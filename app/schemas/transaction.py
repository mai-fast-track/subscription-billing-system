"""
Transaction schemas
"""

import enum
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    PAYMENT = "payment"
    REFUND = "refund"
    BONUS = "bonus"
    PENALTY = "penalty"


class TransactionBase(BaseModel):
    type: str
    amount: int
    description: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class Transaction(TransactionBase):
    id: int
    user_id: int
    payment_id: Optional[int] = None
    balance_before: int
    balance_after: int
    created_at: datetime

    class Config:
        from_attributes = True
