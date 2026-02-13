"""Add user_memories table for cross-session AI memory

Revision ID: 008_add_user_memories
Revises: 007_enhance_market_indicators
Create Date: 2026-02-13

Adds:
- user_memories table: stores AI conversation memory per user (budget, preferences, etc.)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008_add_user_memories'
down_revision = '007_enhance_market_indicators'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add user_memories table for cross-session AI memory persistence.
    Allows the AI to remember budget, preferences, deal-breakers across sessions.
    """
    op.create_table(
        'user_memories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('memory_json', sa.Text(), nullable=True),
        sa.Column('budget_min', sa.Integer(), nullable=True),
        sa.Column('budget_max', sa.Integer(), nullable=True),
        sa.Column('preferred_areas', sa.String(), nullable=True),
        sa.Column('investment_vs_living', sa.String(), nullable=True),
        sa.Column('preferences_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )
    
    # Indexes
    op.create_index('ix_user_memories_id', 'user_memories', ['id'], unique=False)
    op.create_index('ix_user_memories_user_id', 'user_memories', ['user_id'], unique=True)


def downgrade() -> None:
    """Remove user_memories table."""
    op.drop_index('ix_user_memories_user_id', table_name='user_memories')
    op.drop_index('ix_user_memories_id', table_name='user_memories')
    op.drop_table('user_memories')
