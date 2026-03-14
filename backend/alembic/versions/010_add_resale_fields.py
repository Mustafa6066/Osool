"""Add resale and Nawy Now fields to properties

Revision ID: 010_add_resale_fields
Revises: 009_add_gamification_tables
Create Date: 2026-07-01

Adds to properties table:
- is_delivered (boolean) — property already delivered/ready to move
- is_cash_only (boolean) — no installments, cash payment only
- land_area (integer) — land area in sqm (separate from BUA size_sqm)
- nawy_reference (varchar) — Nawy property ID from URL
- is_nawy_now (boolean) — Nawy mortgage product
- scraped_at (timestamptz) — last scrape timestamp
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '010_add_resale_fields'
down_revision = '009_add_gamification_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add resale/delivery columns to properties table (idempotent)."""

    # is_delivered
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE properties ADD COLUMN is_delivered BOOLEAN DEFAULT FALSE;
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)

    # is_cash_only
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE properties ADD COLUMN is_cash_only BOOLEAN DEFAULT FALSE;
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)

    # land_area
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE properties ADD COLUMN land_area INTEGER;
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)

    # nawy_reference
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE properties ADD COLUMN nawy_reference VARCHAR;
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)

    # is_nawy_now
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE properties ADD COLUMN is_nawy_now BOOLEAN DEFAULT FALSE;
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)

    # scraped_at
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE properties ADD COLUMN scraped_at TIMESTAMPTZ;
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)

    # Create index on sale_type for fast filtering
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_properties_sale_type ON properties (sale_type);
    """)

    # Create index on is_delivered for fast "ready to move" queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_properties_is_delivered ON properties (is_delivered);
    """)

    # Create index on is_nawy_now
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_properties_is_nawy_now ON properties (is_nawy_now);
    """)

    # Create index on nawy_reference for dedup
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_properties_nawy_reference ON properties (nawy_reference);
    """)

    # Backfill: Mark properties with delivery_date containing past years or 'Delivered' as delivered
    op.execute("""
        UPDATE properties
        SET is_delivered = TRUE
        WHERE delivery_date IN ('Delivered', '2020', '2021', '2022', '2023', '2024')
          AND (is_delivered IS NULL OR is_delivered = FALSE);
    """)


def downgrade() -> None:
    """Remove resale columns."""
    op.execute("ALTER TABLE properties DROP COLUMN IF EXISTS is_delivered;")
    op.execute("ALTER TABLE properties DROP COLUMN IF EXISTS is_cash_only;")
    op.execute("ALTER TABLE properties DROP COLUMN IF EXISTS land_area;")
    op.execute("ALTER TABLE properties DROP COLUMN IF EXISTS nawy_reference;")
    op.execute("ALTER TABLE properties DROP COLUMN IF EXISTS is_nawy_now;")
    op.execute("ALTER TABLE properties DROP COLUMN IF EXISTS scraped_at;")
    op.execute("DROP INDEX IF EXISTS idx_properties_sale_type;")
    op.execute("DROP INDEX IF EXISTS idx_properties_is_delivered;")
    op.execute("DROP INDEX IF EXISTS idx_properties_is_nawy_now;")
    op.execute("DROP INDEX IF EXISTS idx_properties_nawy_reference;")
