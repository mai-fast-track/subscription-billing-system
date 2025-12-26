"""add saved_payment_method_id to users

Revision ID: add_saved_payment_method
Revises:
Create Date: 2025-01-16 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "add_saved_payment_method"
down_revision = "65905bba8a82"  # latest_version
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем поле saved_payment_method_id в таблицу users
    op.add_column("users", sa.Column("saved_payment_method_id", sa.String(length=255), nullable=True))
    # Создаем индекс для быстрого поиска
    op.create_index(op.f("ix_users_saved_payment_method_id"), "users", ["saved_payment_method_id"], unique=False)


def downgrade() -> None:
    # Удаляем индекс
    op.drop_index(op.f("ix_users_saved_payment_method_id"), table_name="users")
    # Удаляем поле
    op.drop_column("users", "saved_payment_method_id")
