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
    op.execute("ALTER TABLE properties ADD COLUMN IF NOT EXISTS osool_score FLOAT")
    op.execute("ALTER TABLE properties ADD COLUMN IF NOT EXISTS bargain_percentage FLOAT")
    op.execute("ALTER TABLE properties ADD COLUMN IF NOT EXISTS url VARCHAR(500)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_properties_url ON properties (url)")

def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_properties_url")
    op.execute("ALTER TABLE properties DROP COLUMN IF EXISTS url")
    op.execute("ALTER TABLE properties DROP COLUMN IF EXISTS bargain_percentage")
    op.execute("ALTER TABLE properties DROP COLUMN IF EXISTS osool_score")
