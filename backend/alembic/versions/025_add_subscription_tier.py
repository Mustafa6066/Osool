"""Add subscription_tier to users

Revision ID: 025_add_subscription_tier
Revises: 024_hallucination_flags
Create Date: 2026-05-10
"""

from alembic import op
import sqlalchemy as sa


revision = "025_add_subscription_tier"
down_revision = "024_hallucination_flags"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("subscription_tier", sa.String(length=20), nullable=False, server_default="free"),
    )


def downgrade():
    op.drop_column("users", "subscription_tier")
