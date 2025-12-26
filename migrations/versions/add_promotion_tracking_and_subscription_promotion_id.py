"""add promotion tracking and subscription promotion_id

Revision ID: add_promotion_tracking
Revises: ee751218a81d
Create Date: 2025-01-27 16:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "add_promotion_tracking"
down_revision = "create_refunds_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создаем таблицу user_promotion_usage
    op.create_table(
        "user_promotion_usage",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("promotion_id", sa.Integer(), nullable=False),
        sa.Column("subscription_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["promotion_id"], ["promotions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "promotion_id", name="uq_user_promotion"),
    )
    # Создаем индексы для user_promotion_usage
    op.create_index(op.f("ix_user_promotion_usage_user_id"), "user_promotion_usage", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_user_promotion_usage_promotion_id"), "user_promotion_usage", ["promotion_id"], unique=False
    )
    op.create_index(
        op.f("ix_user_promotion_usage_subscription_id"), "user_promotion_usage", ["subscription_id"], unique=False
    )

    # Добавить promotion_id в subscriptions
    op.add_column("subscriptions", sa.Column("promotion_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_subscriptions_promotion_id", "subscriptions", "promotions", ["promotion_id"], ["id"], ondelete="SET NULL"
    )
    op.create_index(op.f("ix_subscriptions_promotion_id"), "subscriptions", ["promotion_id"], unique=False)


def downgrade() -> None:
    # Удаляем promotion_id из subscriptions
    op.drop_index(op.f("ix_subscriptions_promotion_id"), table_name="subscriptions")
    op.drop_constraint("fk_subscriptions_promotion_id", "subscriptions", type_="foreignkey")
    op.drop_column("subscriptions", "promotion_id")

    # Удаляем индексы и таблицу user_promotion_usage
    op.drop_index(op.f("ix_user_promotion_usage_subscription_id"), table_name="user_promotion_usage")
    op.drop_index(op.f("ix_user_promotion_usage_promotion_id"), table_name="user_promotion_usage")
    op.drop_index(op.f("ix_user_promotion_usage_user_id"), table_name="user_promotion_usage")
    op.drop_table("user_promotion_usage")
