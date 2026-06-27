"""Build the HNSW index on properties.embedding (vector search was seq-scanning)

Revision ID: 043_build_hnsw_embedding_index
Revises: 042_add_property_source
Create Date: 2026-06-27

Migration 023 tried to create ix_properties_embedding_hnsw but (a) the column was
still TEXT then so it couldn't, and (b) it swallowed the failure. 034 converted the
column to vector(1536) but SPLIT the index build out to a manual `railway ssh` step
that is easy to forget. So in practice the index is ABSENT and every vector query is
a full sequential cosine scan over ~22K x 1536 (re-run up to 3x by the retrieval
relaxation ladder). [audit I25]

This builds it. The 023/034 attempts hit `/dev/shm` "No space left on device" from
PARALLEL maintenance workers' shared-memory segments, so we DISABLE parallel build
for this statement (single-worker is slower but fits the shared-memory budget — the
real root cause, not work_mem). The build is wrapped so a failure WARNs rather than
crash-looping the deploy; the startup probe (X1, app/main.py) then makes a missing
index LOUD (Sentry + osool_pgvector_available gauge) instead of silent seq-scans.

Idempotent: CREATE INDEX IF NOT EXISTS, guarded on the column being a real vector
type (no-op when pgvector is unavailable and the column is still the TEXT fallback).

NOTE: a failed build is swallowed (WARNING) so the deploy doesn't crash-loop — which
means Alembic still records 043 as APPLIED and `alembic upgrade head` will NOT retry
it. Recovery = act on the X1 probe alert with a MANUAL rebuild (034's docstring has
the `railway ssh ... CREATE INDEX ... USING hnsw` recipe; keep parallel workers off).
"""
from alembic import op


revision = "043_build_hnsw_embedding_index"
down_revision = "042_add_property_source"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Single-worker build to avoid the /dev/shm exhaustion the prior attempts hit.
    # Use plain SET (session), NOT SET LOCAL: under the async (asyncpg) migration
    # runner SET LOCAL did NOT constrain the build in practice — the index silently
    # failed to build in prod (2026-06-27) and had to be created manually with a
    # session-level SET. SET LOCAL only takes effect inside an open transaction
    # block; session SET reliably applies to the CREATE INDEX below on this
    # connection. 043 is the head migration, so leaking these settings to a later
    # migration is not a concern.
    op.execute("SET max_parallel_maintenance_workers = 0")
    op.execute("SET maintenance_work_mem = '256MB'")
    # A single-worker HNSW build is slow — don't let a role/connection
    # statement_timeout cancel it mid-build (the DO block would swallow that and
    # leave the index absent). Bound the table-lock wait so contention with a
    # scraper write fails fast (warn + X1 alerts) instead of hanging the deploy.
    op.execute("SET statement_timeout = 0")
    op.execute("SET lock_timeout = '10s'")
    op.execute(
        """
        DO $$
        BEGIN
            -- Only index a real vector column (no-op if pgvector is unavailable and
            -- the column is still the TEXT fallback from models.py).
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'properties'
                  AND column_name = 'embedding'
                  AND udt_name = 'vector'
            ) THEN
                CREATE INDEX IF NOT EXISTS ix_properties_embedding_hnsw
                ON properties USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64);
                RAISE NOTICE 'HNSW index present';
            ELSE
                RAISE WARNING 'embedding is not a vector column — HNSW index skipped';
            END IF;
        EXCEPTION WHEN OTHERS THEN
            -- Don't crash-loop the deploy; the X1 startup probe alerts on absence.
            RAISE WARNING 'HNSW index build failed (vector search stays seq-scan): %', SQLERRM;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_properties_embedding_hnsw")
