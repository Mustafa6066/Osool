"""Add conversation_analytics table for AI tracking

Revision ID: 004_add_conversation_analytics
Revises: 003_add_encrypted_wallet
Create Date: 2026-01-12

Phase 3: AI Personality Enhancement - Conversation Analytics
Tracks AI agent performance for optimization and conversion analysis.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '004_add_conversation_analytics'
down_revision = '003_add_encrypted_wallet'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create conversation_analytics table for tracking AI agent conversations.

    Features:
    - Customer segmentation tracking (luxury, first_time, savvy)
    - Lead temperature classification (hot, warm, cold)
    - Behavior tracking (properties viewed, tools used, objections)
    - Conversion metrics (reservation generated, viewing scheduled)
    - Engagement metrics (session duration, message count)

    Used for: A/B testing, conversion optimization, lead scoring validation
    """
    op.create_table(
        'conversation_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),

        # Segmentation fields
        sa.Column('customer_segment', sa.String(), nullable=True),
        sa.Column('lead_temperature', sa.String(), nullable=True),
        sa.Column('lead_score', sa.Integer(), server_default='0', nullable=False),

        # Behavior tracking
        sa.Column('properties_viewed', sa.Integer(), server_default='0', nullable=False),
        sa.Column('tools_used', sa.String(), nullable=True),  # JSON string
        sa.Column('objections_raised', sa.String(), nullable=True),  # JSON string

        # Outcome metrics
        sa.Column('conversion_status', sa.String(), server_default='browsing', nullable=False),
        sa.Column('reservation_generated', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('viewing_scheduled', sa.Boolean(), server_default='false', nullable=False),

        # Engagement metrics
        sa.Column('session_duration_seconds', sa.Integer(), server_default='0', nullable=False),
        sa.Column('message_count', sa.Integer(), server_default='0', nullable=False),

        # Additional context
        sa.Column('user_intent', sa.String(), nullable=True),
        sa.Column('budget_mentioned', sa.Integer(), nullable=True),
        sa.Column('preferred_locations', sa.String(), nullable=True),  # JSON string

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for performance
    op.create_index('ix_conversation_analytics_session_id', 'conversation_analytics', ['session_id'], unique=True)
    op.create_index('ix_conversation_analytics_user_id', 'conversation_analytics', ['user_id'], unique=False)
    op.create_index('ix_conversation_analytics_customer_segment', 'conversation_analytics', ['customer_segment'], unique=False)
    op.create_index('ix_conversation_analytics_lead_temperature', 'conversation_analytics', ['lead_temperature'], unique=False)
    op.create_index('ix_conversation_analytics_created_at', 'conversation_analytics', ['created_at'], unique=False)


def downgrade() -> None:
    """
    Remove conversation_analytics table.

    WARNING: This will permanently delete all conversation analytics data!
    Ensure you have backups before running this downgrade.
    """
    op.drop_index('ix_conversation_analytics_created_at', table_name='conversation_analytics')
    op.drop_index('ix_conversation_analytics_lead_temperature', table_name='conversation_analytics')
    op.drop_index('ix_conversation_analytics_customer_segment', table_name='conversation_analytics')
    op.drop_index('ix_conversation_analytics_user_id', table_name='conversation_analytics')
    op.drop_index('ix_conversation_analytics_session_id', table_name='conversation_analytics')
    op.drop_table('conversation_analytics')
