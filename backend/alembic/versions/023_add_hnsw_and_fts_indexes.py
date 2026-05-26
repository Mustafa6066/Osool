"""Add HNSW vector index and full-text search infrastructure

Revision ID: 023_add_hnsw_and_fts_indexes
Revises: 022_add_portfolios_table
Create Date: 2026-03-19

Performance optimization:
- HNSW index on embedding column (replaces sequential scan with ANN)
- tsvector generated column + GIN index for BM25-style full-text search
- pg_trgm trigram index on compound for fuzzy matching
"""

from alembic import op
import sqlalchemy as sa

revision = "023_add_hnsw_and_fts_indexes"
down_revision = "022_add_portfolios_table"
branch_labels = None
depends_on = None


def upgrade():
    # Each operation is wrapped in a PL/pgSQL DO block with exception handling
    # so that individual failures don't crash the entire migration.
    # This prevents container crash-loops on Railway when an operation
    # fails (e.g., missing extension, wrong column type, permissions).

    # 1. HNSW index on embedding column for approximate nearest neighbor search
    op.execute("""
        DO $$ BEGIN
            CREATE INDEX IF NOT EXISTS ix_properties_embedding_hnsw
            ON properties
            USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
            RAISE NOTICE 'HNSW index created';
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'HNSW index skipped: %', SQLERRM;
        END $$;
    """)

    # 2. Generated tsvector column for full-text search (BM25-like ranking)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE properties
            ADD COLUMN IF NOT EXISTS search_tsv tsvector
            GENERATED ALWAYS AS (
                setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(compound, '')), 'B') ||
                setweight(to_tsvector('english', coalesce(location, '')), 'B') ||
                setweight(to_tsvector('english', coalesce(developer, '')), 'C') ||
                setweight(to_tsvector('english', coalesce(description, '')), 'D')
            ) STORED;
            RAISE NOTICE 'FTS tsvector column created';
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'FTS tsvector column skipped: %', SQLERRM;
        END $$;
    """)

    # 3. GIN index on tsvector column (only if the column exists)
    op.execute("""
        DO $$ BEGIN
            CREATE INDEX IF NOT EXISTS ix_properties_search_tsv
            ON properties USING gin (search_tsv);
            RAISE NOTICE 'FTS GIN index created';
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'FTS GIN index skipped: %', SQLERRM;
        END $$;
    """)

    # 4. pg_trgm extension + trigram index for fuzzy compound name matching
    op.execute("""
        DO $$ BEGIN
            CREATE EXTENSION IF NOT EXISTS pg_trgm;
            RAISE NOTICE 'pg_trgm extension created';
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'pg_trgm extension skipped: %', SQLERRM;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE INDEX IF NOT EXISTS ix_properties_compound_trgm
            ON properties USING gin (compound gin_trgm_ops);
            RAISE NOTICE 'Trigram index created';
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'Trigram index skipped: %', SQLERRM;
        END $$;
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_properties_compound_trgm;")
    op.execute("DROP INDEX IF EXISTS ix_properties_search_tsv;")
    op.execute("ALTER TABLE properties DROP COLUMN IF EXISTS search_tsv;")
    op.execute("DROP INDEX IF EXISTS ix_properties_embedding_hnsw;")
