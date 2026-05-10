"""Add zero token fields to property

Revision ID: 014_add_zero_token_fields
Revises: 013_add_ticketing_system
Create Date: 2026-05-09 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '014_add_zero_token_fields'
down_revision = '013_add_ticketing_system'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add columns to properties table
    op.add_column('properties', sa.Column('osool_score', sa.Float(), nullable=True))
    op.add_column('properties', sa.Column('bargain_percentage', sa.Float(), nullable=True))
    op.add_column('properties', sa.Column('url', sa.String(length=500), nullable=True))

    # Create unique constraint for URL if supported or fallback to standard index
    # We create unique constraint on Postgres usually
    # op.create_unique_constraint('uq_properties_url', 'properties', ['url'])
    op.create_index('ix_properties_url', 'properties', ['url'], unique=True)

def downgrade() -> None:
    # Drop columns
    op.drop_index('ix_properties_url', table_name='properties')
    op.drop_column('properties', 'url')
    op.drop_column('properties', 'bargain_percentage')
    op.drop_column('properties', 'osool_score')
