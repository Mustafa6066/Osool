"""Initial schema with all Osool models

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-01-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('national_id', sa.String(), nullable=True),
        sa.Column('wallet_address', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('password_hash', sa.String(), nullable=True),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('phone_number', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=False, server_default='investor'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('phone_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verification_token', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_national_id', 'users', ['national_id'], unique=True)
    op.create_index('ix_users_wallet_address', 'users', ['wallet_address'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Properties table
    op.create_table('properties',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', sa.String(), nullable=True),
        sa.Column('location', sa.String(), nullable=False),
        sa.Column('compound', sa.String(), nullable=True),
        sa.Column('developer', sa.String(), nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('price_per_sqm', sa.Float(), nullable=True),
        sa.Column('size_sqm', sa.Integer(), nullable=False),
        sa.Column('bedrooms', sa.Integer(), nullable=False),
        sa.Column('bathrooms', sa.Integer(), nullable=True),
        sa.Column('finishing', sa.String(), nullable=True),
        sa.Column('delivery_date', sa.String(), nullable=True),
        sa.Column('down_payment', sa.Integer(), nullable=True),
        sa.Column('installment_years', sa.Integer(), nullable=True),
        sa.Column('monthly_installment', sa.Float(), nullable=True),
        sa.Column('image_url', sa.Text(), nullable=True),
        sa.Column('nawy_url', sa.Text(), nullable=True),
        sa.Column('sale_type', sa.String(), nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('blockchain_id', sa.Integer(), nullable=True),
        sa.Column('is_available', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_properties_id', 'properties', ['id'])
    op.create_index('ix_properties_title', 'properties', ['title'])
    op.create_index('ix_properties_location', 'properties', ['location'])
    op.create_index('ix_properties_blockchain_id', 'properties', ['blockchain_id'], unique=True)

    # Transactions table
    op.create_table('transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(), nullable=False, server_default='EGP'),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('paymob_order_id', sa.String(), nullable=True),
        sa.Column('blockchain_tx_hash', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_transactions_id', 'transactions', ['id'])

    # Payment Approvals table
    op.create_table('payment_approvals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('reference_number', sa.String(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_payment_approvals_id', 'payment_approvals', ['id'])
    op.create_index('ix_payment_approvals_reference_number', 'payment_approvals', ['reference_number'], unique=True)

    # Chat Messages table
    op.create_table('chat_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('properties_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chat_messages_id', 'chat_messages', ['id'])
    op.create_index('ix_chat_messages_session_id', 'chat_messages', ['session_id'])

    # Refresh Tokens table (Phase 6)
    op.create_table('refresh_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_refresh_tokens_id', 'refresh_tokens', ['id'])
    op.create_index('ix_refresh_tokens_token', 'refresh_tokens', ['token'], unique=True)
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])

    # Liquidity Pools table (Phase 6)
    op.create_table('liquidity_pools',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('pool_address', sa.String(), nullable=False),
        sa.Column('token_reserve', sa.Float(), nullable=False, server_default='0'),
        sa.Column('egp_reserve', sa.Float(), nullable=False, server_default='0'),
        sa.Column('total_lp_tokens', sa.Float(), nullable=False, server_default='0'),
        sa.Column('total_volume_24h', sa.Float(), nullable=False, server_default='0'),
        sa.Column('total_fees_earned', sa.Float(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_liquidity_pools_id', 'liquidity_pools', ['id'])
    op.create_index('ix_liquidity_pools_property_id', 'liquidity_pools', ['property_id'], unique=True)
    op.create_index('ix_liquidity_pools_pool_address', 'liquidity_pools', ['pool_address'], unique=True)

    # Trades table (Phase 6)
    op.create_table('trades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pool_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('trade_type', sa.String(), nullable=False),
        sa.Column('token_amount', sa.Float(), nullable=False),
        sa.Column('egp_amount', sa.Float(), nullable=False),
        sa.Column('execution_price', sa.Float(), nullable=False),
        sa.Column('slippage_percent', sa.Float(), nullable=False),
        sa.Column('fee_amount', sa.Float(), nullable=False),
        sa.Column('tx_hash', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['pool_id'], ['liquidity_pools.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_trades_id', 'trades', ['id'])
    op.create_index('ix_trades_pool_id', 'trades', ['pool_id'])
    op.create_index('ix_trades_user_id', 'trades', ['user_id'])

    # Liquidity Positions table (Phase 6)
    op.create_table('liquidity_positions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('pool_id', sa.Integer(), nullable=False),
        sa.Column('lp_tokens', sa.Float(), nullable=False),
        sa.Column('initial_token_amount', sa.Float(), nullable=False),
        sa.Column('initial_egp_amount', sa.Float(), nullable=False),
        sa.Column('fees_earned', sa.Float(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['pool_id'], ['liquidity_pools.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_liquidity_positions_id', 'liquidity_positions', ['id'])
    op.create_index('ix_liquidity_positions_user_id', 'liquidity_positions', ['user_id'])
    op.create_index('ix_liquidity_positions_pool_id', 'liquidity_positions', ['pool_id'])


def downgrade() -> None:
    op.drop_table('liquidity_positions')
    op.drop_table('trades')
    op.drop_table('liquidity_pools')
    op.drop_table('refresh_tokens')
    op.drop_table('chat_messages')
    op.drop_table('payment_approvals')
    op.drop_table('transactions')
    op.drop_table('properties')
    op.drop_table('users')
    op.execute('DROP EXTENSION IF EXISTS vector')
