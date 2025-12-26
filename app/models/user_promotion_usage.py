"""
UserPromotionUsage model - отслеживание использования промокодов пользователями
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint, func

from app.core.database import Base


class UserPromotionUsage(Base):
    __tablename__ = "user_promotion_usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    promotion_id = Column(Integer, ForeignKey("promotions.id", ondelete="CASCADE"), nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Уникальное ограничение: один пользователь может использовать промокод только один раз
    __table_args__ = (UniqueConstraint("user_id", "promotion_id", name="uq_user_promotion"),)

    def __repr__(self):
        return f"<UserPromotionUsage(id={self.id}, user_id={self.user_id}, promotion_id={self.promotion_id})>"
