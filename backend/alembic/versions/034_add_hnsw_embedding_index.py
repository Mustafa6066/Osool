"""Convert properties.embedding TEXT -> vector(1536)

Revision ID: 034_add_hnsw_embedding_index
Revises: 033_add_delivery_year
Create Date: 2026-05-27

The properties.embedding column was originally TEXT (models.py fallback
for environments without pgvector). pgvector IS installed on Railway
(0.8.2) and 444 rows already contain JSON-stringified 1536-dim vectors.

This migration converts the column to vector(1536) so the L2d
'more like this' path in property_retrieval.py can do cosine similarity
on it (and so future HNSW indexing has the right type to index).

Note: the HNSW index that was originally bundled with this migration
has been SPLIT OUT into a separate manual step. Railway's Postgres
container hits 'No space left on device' on the shared memory segment
during CREATE INDEX ... USING hnsw, regardless of row count. The index
is a performance optimization (sequential cosine scan at 22K rows is
~150ms p99); it's not load-bearing for correctness. Add it later via:

  railway ssh --service Postgres -- "psql \$DATABASE_URL -c \"
    SET maintenance_work_mem = '512MB';
    CREATE INDEX ix_properties_embedding_hnsw
    ON properties USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);\""

Or, on a larger Postgres plan with bigger /dev/shm, add a follow-up
migration that does the same CREATE INDEX.

Idempotent: DO-block no-ops when the column is already vector(1536).
"""
from alembic import op


revision = "034_add_hnsw_embedding_index"
down_revision = "033_add_delivery_year"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make sure the extension is enabled.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Convert TEXT -> vector(1536) only if it's currently TEXT.
    # The existing TEXT values are JSON-array form '[v1,v2,...]' which
    # pgvector accepts as a text-form vector. NULL stays NULL.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'properties'
                  AND column_name = 'embedding'
                  AND udt_name = 'text'
            ) THEN
                ALTER TABLE properties
                ALTER COLUMN embedding TYPE vector(1536)
                USING embedding::vector(1536);
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'properties'
                  AND column_name = 'embedding'
                  AND udt_name = 'vector'
            ) THEN
                ALTER TABLE properties
                ALTER COLUMN embedding TYPE text
                USING embedding::text;
            END IF;
        END
        $$;
        """
    )
