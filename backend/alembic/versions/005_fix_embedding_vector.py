"""Fix embedding column type from TEXT to VECTOR(1536)

Revision ID: 005_fix_embedding_vector
Revises: 004_add_conversation_analytics
Create Date: 2026-01-17

This migration fixes the embedding column type in the properties table.
The column was created as TEXT when pgvector wasn't available, but now
needs to be VECTOR(1536) for proper cosine similarity search.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005_fix_embedding_vector'
down_revision = '004_add_conversation_analytics'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Convert embedding column from TEXT to VECTOR(1536).
    
    IMPORTANT: This migration will SKIP on PostgreSQL instances without pgvector.
    Vector search will fall back to text search in those environments.
    """
    import os
    from sqlalchemy import text
    from alembic import op
    
    # Check if pgvector is available on the database
    conn = op.get_bind()
    
    try:
        # Test if vector extension can be created
        result = conn.execute(text("""
            SELECT * FROM pg_available_extensions WHERE name = 'vector'
        """))
        pgvector_available = result.fetchone() is not None
    except Exception:
        pgvector_available = False
    
    if not pgvector_available:
        print("⚠️ pgvector extension not available on this PostgreSQL instance.")
        print("⚠️ Vector search will use TEXT fallback. This is OK for development.")
        print("⚠️ For production vector search, use Supabase, Neon, or pgvector-enabled PostgreSQL.")
        return  # Skip the migration entirely
    
    # If we get here, pgvector IS available
    print("🔧 Enabling pgvector extension...")
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Step 2: Check if column is TEXT and needs conversion
    # We'll use raw SQL for the type conversion
    print("🔧 Converting embedding column from TEXT to VECTOR(1536)...")
    
    # This handles the case where embedding is stored as TEXT (JSON array string)
    # We need to:
    # 1. Add a new vector column
    # 2. Parse the JSON text into vector
    # 3. Drop old column and rename new one
    
    op.execute("""
        -- Add temporary vector column
        ALTER TABLE properties 
        ADD COLUMN IF NOT EXISTS embedding_vector vector(1536);
    """)
    
    op.execute("""
        -- Convert TEXT JSON to VECTOR for rows that have embeddings
        UPDATE properties 
        SET embedding_vector = embedding::vector(1536)
        WHERE embedding IS NOT NULL 
        AND embedding != ''
        AND embedding ~ '^\[.*\]$';
    """)
    
    op.execute("""
        -- Drop the old TEXT column
        ALTER TABLE properties 
        DROP COLUMN IF EXISTS embedding;
    """)
    
    op.execute("""
        -- Rename the new vector column to 'embedding'
        ALTER TABLE properties 
        RENAME COLUMN embedding_vector TO embedding;
    """)
    
    print("✅ Embedding column converted to VECTOR(1536) successfully!")


def downgrade() -> None:
    """
    Revert embedding column from VECTOR(1536) back to TEXT.
    Note: This will lose the ability to do cosine similarity search.
    """
    print("⚠️ Downgrading embedding column from VECTOR to TEXT...")
    
    op.execute("""
        -- Add temporary text column
        ALTER TABLE properties 
        ADD COLUMN IF NOT EXISTS embedding_text TEXT;
    """)
    
    op.execute("""
        -- Convert VECTOR to TEXT (JSON array format)
        UPDATE properties 
        SET embedding_text = embedding::text
        WHERE embedding IS NOT NULL;
    """)
    
    op.execute("""
        -- Drop the vector column
        ALTER TABLE properties 
        DROP COLUMN IF EXISTS embedding;
    """)
    
    op.execute("""
        -- Rename the text column back to 'embedding'
        ALTER TABLE properties 
        RENAME COLUMN embedding_text TO embedding;
    """)
    
    print("✅ Embedding column reverted to TEXT.")
