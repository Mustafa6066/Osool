"""Add KYC fields to User model

Revision ID: 002_add_kyc_fields
Revises: 001_initial_schema
Create Date: 2026-01-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_kyc_fields'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new KYC tracking columns
    op.add_column('users', sa.Column('kyc_status', sa.String(), nullable=False, server_default='pending'))
    op.add_column('users', sa.Column('kyc_verified_at', sa.DateTime(timezone=True), nullable=True))

    # Note: We're NOT making national_id and phone_number non-nullable yet
    # to maintain backward compatibility with existing users.
    # New signups will enforce these fields at the application level.
    # In a future migration, we can add NOT NULL constraints after data backfill.


def downgrade() -> None:
    op.drop_column('users', 'kyc_verified_at')
    op.drop_column('users', 'kyc_status')
