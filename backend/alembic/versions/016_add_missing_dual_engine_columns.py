"""Add missing columns to dual-engine tables

Revision ID: 016_add_missing_dual_engine_columns
Revises: 015_add_dual_engine_models
Create Date: 2026-03-09

Adds columns:
- chat_intents.user_id (FK -> users.id, nullable, indexed)
- lead_profiles.stage (varchar(30), default 'new')
- email_events.email_type (varchar(100), nullable)
- email_events.subject (varchar(500), nullable)
- email_events.resend_id (varchar(200), nullable, indexed)
- seo_pages.content_json (text, nullable)
"""
from alembic import op
import sqlalchemy as sa


revision = '016_add_missing_dual_engine_columns'
down_revision = '015_add_dual_engine_models'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # chat_intents.user_id
    op.add_column('chat_intents', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_index('ix_chat_intents_user_id', 'chat_intents', ['user_id'])
    op.create_foreign_key(
        'fk_chat_intents_user_id', 'chat_intents', 'users',
        ['user_id'], ['id'], ondelete='SET NULL',
    )

    # lead_profiles.stage
    op.add_column('lead_profiles', sa.Column('stage', sa.String(30), server_default='new', nullable=False))

    # email_events – three new columns
    op.add_column('email_events', sa.Column('email_type', sa.String(100), nullable=True))
    op.add_column('email_events', sa.Column('subject', sa.String(500), nullable=True))
    op.add_column('email_events', sa.Column('resend_id', sa.String(200), nullable=True))
    op.create_index('ix_email_events_resend_id', 'email_events', ['resend_id'])

    # seo_pages.content_json
    op.add_column('seo_pages', sa.Column('content_json', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('seo_pages', 'content_json')
    op.drop_index('ix_email_events_resend_id', table_name='email_events')
    op.drop_column('email_events', 'resend_id')
    op.drop_column('email_events', 'subject')
    op.drop_column('email_events', 'email_type')
    op.drop_column('lead_profiles', 'stage')
    op.drop_constraint('fk_chat_intents_user_id', 'chat_intents', type_='foreignkey')
    op.drop_index('ix_chat_intents_user_id', table_name='chat_intents')
    op.drop_column('chat_intents', 'user_id')
