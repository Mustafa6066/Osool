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
    # 1. HNSW index on embedding column for approximate nearest neighbor search
    #    m=16 (connections per node), ef_construction=64 (build-time accuracy)
    #    Uses cosine distance operator class to match existing queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_properties_embedding_hnsw
        ON properties
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)

    # 2. Generated tsvector column for full-text search (BM25-like ranking)
    #    Combines title (weight A), compound+location (weight B), description (weight C)
    op.execute("""
        ALTER TABLE properties
        ADD COLUMN IF NOT EXISTS search_tsv tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(compound, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(location, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(developer, '')), 'C') ||
            setweight(to_tsvector('english', coalesce(description, '')), 'D')
        ) STORED;
    """)

    # 3. GIN index on tsvector column for fast full-text search
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_properties_search_tsv
        ON properties USING gin (search_tsv);
    """)

    # 4. pg_trgm extension + trigram index for fuzzy compound name matching
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_properties_compound_trgm
        ON properties USING gin (compound gin_trgm_ops);
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_properties_compound_trgm;")
    op.execute("DROP INDEX IF EXISTS ix_properties_search_tsv;")
    op.execute("ALTER TABLE properties DROP COLUMN IF EXISTS search_tsv;")
    op.execute("DROP INDEX IF EXISTS ix_properties_embedding_hnsw;")
