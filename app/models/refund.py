from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, func

from app.core.database import Base


class Refund(Base):
    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True, index=True)

    # Связи
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True)

    # Данные возврата
    yookassa_refund_id = Column(String(255), unique=True, nullable=False, index=True)
    # ID возврата в Юкассе

    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="RUB")

    status = Column(String(50), default="pending")  # pending, succeeded, failed, cancelled

    reason = Column(String(500), nullable=True)

    # Логирование
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Refund(id={self.id}, payment_id={self.payment_id}, status={self.status}, amount={self.amount})>"
