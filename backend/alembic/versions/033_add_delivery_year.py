"""Add delivery_year INT column for fast ready-by filtering

Revision ID: 033_add_delivery_year
Revises: 032_subscription_tier_extensions
Create Date: 2026-05-27

The zero-token property retrieval pipeline filters on "ready by year"
(e.g. "show me units delivered by 2025"). Today this would require
parsing the free-text `delivery_date` column at query time, which is
both slow and fragile (values look like "Q3 2024", "2025", "Delivered",
etc.).

This migration adds a clean integer `delivery_year` column with a
B-tree index, then backfills it from `delivery_date` for all existing
rows. The scraper's deterministic_normalizer is updated separately
(in a later commit) to write this column on every upsert.

Idempotent: ADD COLUMN IF NOT EXISTS + CREATE INDEX IF NOT EXISTS.
"""
from alembic import op


revision = "033_add_delivery_year"
down_revision = "032_subscription_tier_extensions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Add the column (idempotent)
    op.execute(
        """
        ALTER TABLE properties
        ADD COLUMN IF NOT EXISTS delivery_year INTEGER
        """
    )

    # 2) B-tree index for the ready-by filter
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_properties_delivery_year
        ON properties (delivery_year)
        """
    )

    # 3) Backfill from existing delivery_date text.
    # Patterns to handle, in priority order:
    #   "Q3 2024" / "Q4 2025"   -> 2024 / 2025
    #   "2024-09-15" / "2024-09" -> 2024
    #   "2025"                    -> 2025
    #   "Delivered" / "Ready"     -> previous year (current_year - 1)
    # Anything else stays NULL.
    op.execute(
        r"""
        UPDATE properties
        SET delivery_year = CASE
            WHEN delivery_date ~* '^Q[1-4]\s+(20\d{2})$'
                THEN CAST(substring(delivery_date FROM '\d{4}') AS INTEGER)
            WHEN delivery_date ~ '^\d{4}-\d{2}'
                THEN CAST(substring(delivery_date FROM '^(\d{4})') AS INTEGER)
            WHEN delivery_date ~ '^\d{4}$'
                THEN CAST(delivery_date AS INTEGER)
            WHEN delivery_date ILIKE '%delivered%' OR delivery_date ILIKE '%ready%'
                THEN EXTRACT(YEAR FROM NOW())::INT - 1
            ELSE NULL
        END
        WHERE delivery_year IS NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_properties_delivery_year")
    op.execute("ALTER TABLE properties DROP COLUMN IF EXISTS delivery_year")
