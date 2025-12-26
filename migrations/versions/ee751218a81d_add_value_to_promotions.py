"""add value to promotions

Revision ID: ee751218a81d
Revises: add_saved_payment_method
Create Date: 2025-01-27 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ee751218a81d"
down_revision = "add_saved_payment_method"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем поле value в таблицу promotions
    # Integer для хранения количества дней (trial, bonus_days) или процента/суммы скидки
    op.add_column("promotions", sa.Column("value", sa.Integer(), nullable=True))


def downgrade() -> None:
    # Удаляем поле value
    op.drop_column("promotions", "value")
