"""Add properties.source column for scoped stale-marking

Revision ID: 042_add_property_source
Revises: 041_free_path_retrieval_indexes
Create Date: 2026-06-26

Phase 0 / catalog-wipe guard (I31). mark_stale_properties() updates the
`properties` table globally with no source/scope predicate, while several
writers (full-catalog Nawy, per-area Nawy, Aqarmap, on-demand worker) register
run_ids into one shared 2-slot Redis window. Without a per-row source we cannot
scope stale-marking to "only the feed that just refreshed" (I6) — a narrow
Aqarmap or per-area run could otherwise delist the entire broad catalog.

This migration adds a nullable `source` VARCHAR(32) with a B-tree index and
backfills existing Nawy rows (identified by a non-null nawy_url) to 'nawy'.
Rows we cannot attribute stay NULL — a source-scoped sweep simply skips them,
which is the safe (never-wrongly-delist) behavior. The scraper upsert path is
updated in the same change to stamp `source` on every insert/update.

Idempotent: ADD COLUMN IF NOT EXISTS + CREATE INDEX IF NOT EXISTS.
"""
from alembic import op


revision = "042_add_property_source"
down_revision = "041_free_path_retrieval_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Add the column (idempotent)
    op.execute(
        """
        ALTER TABLE properties
        ADD COLUMN IF NOT EXISTS source VARCHAR(32)
        """
    )

    # 2) B-tree index used by source-scoped stale-marking
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_properties_source
        ON properties (source)
        """
    )

    # 3) Best-effort backfill: a non-null nawy_url means the row came from Nawy.
    #    Everything else stays NULL (unknown) so a nawy-scoped stale sweep will
    #    never delist a row it cannot attribute.
    op.execute(
        """
        UPDATE properties
        SET source = 'nawy'
        WHERE source IS NULL AND nawy_url IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_properties_source")
    op.execute("ALTER TABLE properties DROP COLUMN IF EXISTS source")
