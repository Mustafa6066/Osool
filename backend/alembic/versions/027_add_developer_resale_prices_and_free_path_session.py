"""Add developer_price/resale_price to properties + free_path_sessions table

Revision ID: 027_add_developer_resale_prices_and_free_path_session
Revises: 026_merge_zero_token_branch
Create Date: 2026-05-17

Adds to properties:
- developer_price (double precision) — primary-market price; backfilled from `price`
  when sale_type IN ('Developer', 'Nawy Now')
- resale_price (double precision) — secondary-market price; backfilled from `price`
  when sale_type = 'Resale'

Adds free_path_sessions table — persists the free-path conversation state machine
keyed by session_id. Owned by the comparison_dialog driver.
"""
from alembic import op
import sqlalchemy as sa


revision = "027_add_developer_resale_prices_and_free_path_session"
down_revision = "026_merge_zero_token_branch"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # developer_price (idempotent — pattern matches 010_add_resale_fields.py)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE properties ADD COLUMN developer_price DOUBLE PRECISION;
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)

    # resale_price
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE properties ADD COLUMN resale_price DOUBLE PRECISION;
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_properties_developer_price
            ON properties (developer_price);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_properties_resale_price
            ON properties (resale_price);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_properties_compound_type
            ON properties (compound, type);
    """)

    # Backfill. 'Nawy Now' rolls into developer_price per the spec — it's a
    # primary-market mortgage product, not a resale listing.
    op.execute("""
        UPDATE properties
           SET developer_price = price
         WHERE sale_type IN ('Developer', 'Nawy Now')
           AND developer_price IS NULL
           AND price IS NOT NULL;
    """)
    op.execute("""
        UPDATE properties
           SET resale_price = price
         WHERE sale_type = 'Resale'
           AND resale_price IS NULL
           AND price IS NOT NULL;
    """)

    # free_path_sessions
    op.execute("""
        CREATE TABLE IF NOT EXISTS free_path_sessions (
            session_id            VARCHAR PRIMARY KEY,
            state                 VARCHAR(32) NOT NULL DEFAULT 'AWAITING_NAMES',
            candidate_names       JSONB,
            mode                  VARCHAR(16),
            property_type_filter  VARCHAR(32),
            comparison_used       BOOLEAN NOT NULL DEFAULT FALSE,
            updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_free_path_sessions_updated_at
            ON free_path_sessions (updated_at);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS free_path_sessions;")
    op.execute("DROP INDEX IF EXISTS idx_properties_compound_type;")
    op.execute("DROP INDEX IF EXISTS idx_properties_resale_price;")
    op.execute("DROP INDEX IF EXISTS idx_properties_developer_price;")
    op.execute("ALTER TABLE properties DROP COLUMN IF EXISTS resale_price;")
    op.execute("ALTER TABLE properties DROP COLUMN IF EXISTS developer_price;")
