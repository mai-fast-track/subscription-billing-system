"""
User model
"""

from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy import Enum as SQLEnum

from app.core.database import Base
from app.core.enums import UserRole


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.client, nullable=False)

    # Сохраненный платежный метод для автоплатежей
    saved_payment_method_id = Column(String(255), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, role={self.role})>"
