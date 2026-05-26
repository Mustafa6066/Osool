"""Add maintenance_fee_pct and delivery_payment columns to properties

Revision ID: 021_add_maintenance_delivery_fields
Revises: 020_fix_nawy_url_empty_string
Create Date: 2026-03-18
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "021_add_maintenance_delivery_fields"
down_revision = "020_fix_nawy_url_empty_string"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("properties", sa.Column("maintenance_fee_pct", sa.Integer(), nullable=True))
    op.add_column("properties", sa.Column("delivery_payment", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("properties", "delivery_payment")
    op.drop_column("properties", "maintenance_fee_pct")
