"""Remove blockchain-related tables (LiquidityPool, Trade, LiquidityPosition)

Revision ID: 012
Revises: 011
Create Date: 2026-03-06 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011_fix_level_column_type'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Remove blockchain tables and blockchain_id column from properties."""
    
    # Drop liquidity_positions table (depends on liquidity_pools)
    op.execute("DROP TABLE IF EXISTS liquidity_positions CASCADE;")
    
    # Drop trades table (depends on liquidity_pools)
    op.execute("DROP TABLE IF EXISTS trades CASCADE;")
    
    # Drop liquidity_pools table
    op.execute("DROP TABLE IF EXISTS liquidity_pools CASCADE;")
    
    # Drop blockchain_id column and index from properties table
    op.execute("DROP INDEX IF EXISTS ix_properties_blockchain_id;")
    op.execute("ALTER TABLE properties DROP COLUMN IF EXISTS blockchain_id;")
    
    # Drop encrypted_private_key from users (blockchain wallet storage)
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS encrypted_private_key;")


def downgrade() -> None:
    """Restore blockchain tables (for rollback if needed)."""
    
    # Note: This downgrade is not recommended for production.
    # It recreates empty tables. Original data would be lost.
    
    # Recreate encrypted_private_key column
    op.execute("""
        ALTER TABLE users ADD COLUMN encrypted_private_key TEXT;
    """)
    
    # Recreate blockchain_id column
    op.execute("""
        ALTER TABLE properties ADD COLUMN blockchain_id INTEGER;
    """)
    op.execute("""
        CREATE UNIQUE INDEX ix_properties_blockchain_id ON properties(blockchain_id);
    """)
    
    # Recreate liquidity_pools table
    op.execute("""
        CREATE TABLE IF NOT EXISTS liquidity_pools (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            token_a VARCHAR(255),
            token_b VARCHAR(255),
            reserve_a NUMERIC,
            reserve_b NUMERIC,
            fee_tier NUMERIC,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
    
    # Recreate trades table
    op.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id SERIAL PRIMARY KEY,
            pool_id INTEGER REFERENCES liquidity_pools(id),
            user_id INTEGER REFERENCES users(id),
            trade_type VARCHAR(50),
            amount_in NUMERIC,
            amount_out NUMERIC,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX ix_trades_id ON trades(id);")
    op.execute("CREATE INDEX ix_trades_pool_id ON trades(pool_id);")
    op.execute("CREATE INDEX ix_trades_user_id ON trades(user_id);")
    
    # Recreate liquidity_positions table
    op.execute("""
        CREATE TABLE IF NOT EXISTS liquidity_positions (
            id SERIAL PRIMARY KEY,
            pool_id INTEGER REFERENCES liquidity_pools(id),
            user_id INTEGER REFERENCES users(id),
            amount_a NUMERIC,
            amount_b NUMERIC,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
