"""add assigned_user_id to promotions

Revision ID: add_assigned_user_id
Revises: add_promotion_tracking
Create Date: 2025-01-27 17:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "add_assigned_user_id"
down_revision = "add_promotion_tracking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавить assigned_user_id в promotions
    op.add_column("promotions", sa.Column("assigned_user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_promotions_assigned_user_id", "promotions", "users", ["assigned_user_id"], ["id"], ondelete="SET NULL"
    )
    op.create_index(op.f("ix_promotions_assigned_user_id"), "promotions", ["assigned_user_id"], unique=False)


def downgrade() -> None:
    # Удаляем assigned_user_id из promotions
    op.drop_index(op.f("ix_promotions_assigned_user_id"), table_name="promotions")
    op.drop_constraint("fk_promotions_assigned_user_id", "promotions", type_="foreignkey")
    op.drop_column("promotions", "assigned_user_id")
