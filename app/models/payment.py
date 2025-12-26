from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, func

from app.core.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    # Связи
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Данные платежа
    yookassa_payment_id = Column(String(255), unique=True, nullable=False, index=True)
    # ID платежа в Касса

    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="RUB")

    status = Column(String(50), default="pending")  # pending, succeeded, failed, cancelled

    payment_method = Column(String(50), nullable=True)

    # Для retry логики
    attempt_number = Column(Integer, default=1)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)

    error_reason = Column(String(500), nullable=True)

    # Идемпотентность (защита от дублей)
    idempotency_key = Column(String(255), unique=True, nullable=False)

    # Логирование
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Payment(id={self.id}, subscription_id={self.subscription_id}, status={self.status})>"
