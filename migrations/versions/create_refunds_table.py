"""create refunds table

Revision ID: create_refunds_table
Revises: ee751218a81d
Create Date: 2025-01-27 15:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "create_refunds_table"
down_revision = "ee751218a81d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создаем таблицу refunds
    op.create_table(
        "refunds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("payment_id", sa.Integer(), nullable=False),
        sa.Column("yookassa_refund_id", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=True, server_default="RUB"),
        sa.Column("status", sa.String(length=50), nullable=True, server_default="pending"),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    # Создаем индексы
    op.create_index(op.f("ix_refunds_payment_id"), "refunds", ["payment_id"], unique=False)
    op.create_index(op.f("ix_refunds_yookassa_refund_id"), "refunds", ["yookassa_refund_id"], unique=True)


def downgrade() -> None:
    # Удаляем индексы
    op.drop_index(op.f("ix_refunds_yookassa_refund_id"), table_name="refunds")
    op.drop_index(op.f("ix_refunds_payment_id"), table_name="refunds")
    # Удаляем таблицу
    op.drop_table("refunds")
