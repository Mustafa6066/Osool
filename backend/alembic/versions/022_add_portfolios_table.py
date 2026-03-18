"""Add portfolios table for V5 Portfolio Expansion Engine

Revision ID: 022_add_portfolios_table
Revises: 021_add_maintenance_delivery_fields
Create Date: 2026-03-18
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "022_add_portfolios_table"
down_revision = "021_add_maintenance_delivery_fields"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "portfolios",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("property_id", sa.Integer(), sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("transaction_id", sa.Integer(), sa.ForeignKey("transactions.id"), nullable=True),
        sa.Column("purchase_price", sa.Float(), nullable=False),
        sa.Column("current_estimated_value", sa.Float(), nullable=False),
        sa.Column("appreciation_pct", sa.Float(), server_default="0.0"),
        sa.Column("equity_paid", sa.Float(), server_default="0.0"),
        sa.Column("monthly_installment", sa.Float(), nullable=True),
        sa.Column("installments_remaining", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), server_default="active"),
        sa.Column("location_zone", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_valuation_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_table("portfolios")
