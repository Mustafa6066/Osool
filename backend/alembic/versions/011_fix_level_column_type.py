"""Fix investor_profiles level column type from INTEGER to VARCHAR

Revision ID: 011_fix_level_column_type
Revises: 010_add_resale_fields
Create Date: 2026-03-02

The original migration 009 created `level INTEGER DEFAULT 1`,
but the SQLAlchemy model defines `level: Mapped[str] = mapped_column(String(20), default="curious")`.
The gamification engine uses string level keys: curious, informed, analyst, strategist, mogul.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '011_fix_level_column_type'
down_revision = '010_add_resale_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Change level column from INTEGER to VARCHAR(20), converting existing int values."""
    # Step 1: Add a temporary column
    op.execute("ALTER TABLE investor_profiles ADD COLUMN level_new VARCHAR(20) DEFAULT 'curious'")

    # Step 2: Convert existing integer values to string level keys
    # Level mapping: 1=curious, 2=informed, 3=analyst, 4=strategist, 5=mogul
    op.execute("""
        UPDATE investor_profiles SET level_new = CASE
            WHEN level = 1 THEN 'curious'
            WHEN level = 2 THEN 'informed'
            WHEN level = 3 THEN 'analyst'
            WHEN level = 4 THEN 'strategist'
            WHEN level = 5 THEN 'mogul'
            ELSE 'curious'
        END
    """)

    # Step 3: Drop old column and rename new one
    op.execute("ALTER TABLE investor_profiles DROP COLUMN level")
    op.execute("ALTER TABLE investor_profiles RENAME COLUMN level_new TO level")

    # Step 4: Set NOT NULL
    op.execute("ALTER TABLE investor_profiles ALTER COLUMN level SET NOT NULL")
    op.execute("ALTER TABLE investor_profiles ALTER COLUMN level SET DEFAULT 'curious'")


def downgrade() -> None:
    """Revert level column back to INTEGER."""
    op.execute("ALTER TABLE investor_profiles ADD COLUMN level_new INTEGER DEFAULT 1")
    op.execute("""
        UPDATE investor_profiles SET level_new = CASE
            WHEN level = 'curious' THEN 1
            WHEN level = 'informed' THEN 2
            WHEN level = 'analyst' THEN 3
            WHEN level = 'strategist' THEN 4
            WHEN level = 'mogul' THEN 5
            ELSE 1
        END
    """)
    op.execute("ALTER TABLE investor_profiles DROP COLUMN level")
    op.execute("ALTER TABLE investor_profiles RENAME COLUMN level_new TO level")
    op.execute("ALTER TABLE investor_profiles ALTER COLUMN level SET NOT NULL")
    op.execute("ALTER TABLE investor_profiles ALTER COLUMN level SET DEFAULT 1")
