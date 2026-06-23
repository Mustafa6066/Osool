"""Indexes for the rewritten zero-token free best-price retrieval path

Revision ID: 041_free_path_retrieval_indexes
Revises: 040_remove_reservation_controls
Create Date: 2026-06-24

The free best-price path (free_tier_gate._fetch_best_price_candidate) was
rewritten to:
  * group developer rows into a per-(compound, lower(type)) cohort (CTE),
  * join each candidate to its cohort once,
  * filter on is_available + bedrooms,
  * ILIKE '%...%' on location / title / compound for the area/compound filters.

These indexes support that shape. The properties table is small (~23k rows),
so plain CREATE INDEX is fast and lock time is negligible; if the table grows
large, re-create these CONCURRENTLY outside a migration instead.

All statements are IF NOT EXISTS so the migration is idempotent and safe to run
even if some trigram indexes already exist from migration 023.
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '041_free_path_retrieval_indexes'
down_revision = '040_remove_reservation_controls'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Trigram extension for ILIKE '%...%' acceleration.
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    # Cohort GROUP BY + candidate JOIN key: (compound, lower(type)) over
    # available rows. Functional index on lower(type) matches the query.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_properties_compound_ltype_avail
        ON properties (compound, lower(type))
        WHERE is_available;
        """
    )

    # Bedroom equality filter on the best-price path.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_properties_bedrooms_avail
        ON properties (bedrooms)
        WHERE is_available;
        """
    )

    # Trigram GIN indexes for the area/compound ILIKE filters.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_properties_location_trgm "
        "ON properties USING gin (location gin_trgm_ops);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_properties_title_trgm "
        "ON properties USING gin (title gin_trgm_ops);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_properties_compound_trgm "
        "ON properties USING gin (compound gin_trgm_ops);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_properties_compound_trgm;")
    op.execute("DROP INDEX IF EXISTS ix_properties_title_trgm;")
    op.execute("DROP INDEX IF EXISTS ix_properties_location_trgm;")
    op.execute("DROP INDEX IF EXISTS ix_properties_bedrooms_avail;")
    op.execute("DROP INDEX IF EXISTS ix_properties_compound_ltype_avail;")
    # pg_trgm extension is left in place — other indexes may depend on it.
