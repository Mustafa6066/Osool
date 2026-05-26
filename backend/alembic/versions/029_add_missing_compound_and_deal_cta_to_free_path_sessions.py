"""Add missing_compound and has_shown_deal_cta to free_path_sessions

Revision ID: 029_add_missing_compound_and_deal_cta
Revises: 028_add_consultation_bookings
Create Date: 2026-05-26

Adds to free_path_sessions:
- missing_compound (VARCHAR 256, nullable) — tracks which compound triggered
  MISSING_DATA so _handle_missing_data replaces the correct entry (CQ1 fix)
- has_shown_deal_cta (BOOLEAN NOT NULL DEFAULT FALSE) — prevents CTA from
  showing more than once per session (D9 timing spec)
"""
from alembic import op


revision = "029_add_missing_compound_and_deal_cta"
down_revision = "028_add_consultation_bookings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE free_path_sessions
                ADD COLUMN missing_compound VARCHAR(256);
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            ALTER TABLE free_path_sessions
                ADD COLUMN has_shown_deal_cta BOOLEAN NOT NULL DEFAULT FALSE;
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE free_path_sessions DROP COLUMN IF EXISTS has_shown_deal_cta;")
    op.execute("ALTER TABLE free_path_sessions DROP COLUMN IF EXISTS missing_compound;")
