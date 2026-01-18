"""Add invitation system tables and columns

Revision ID: 006_add_invitation_system
Revises: 005_fix_embedding_vector
Create Date: 2026-01-19

Adds:
- invitations table for controlled user registration
- invitations_sent column to users table
- invited_by_user_id column to users table
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_add_invitation_system'
down_revision = '005_fix_embedding_vector'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add invitation system:
    1. Add invitations_sent and invited_by_user_id columns to users table
    2. Create invitations table for tracking invitation codes
    """
    
    # Add new columns to users table
    op.add_column('users', sa.Column('invitations_sent', sa.Integer(), server_default='0', nullable=False))
    op.add_column('users', sa.Column('invited_by_user_id', sa.Integer(), nullable=True))
    
    # Add foreign key for invited_by_user_id
    op.create_foreign_key(
        'fk_users_invited_by_user_id',
        'users', 'users',
        ['invited_by_user_id'], ['id']
    )
    
    # Create invitations table
    op.create_table(
        'invitations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(32), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('used_by_user_id', sa.Integer(), nullable=True),
        sa.Column('is_used', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['used_by_user_id'], ['users.id'])
    )
    
    # Create indexes
    op.create_index('ix_invitations_id', 'invitations', ['id'], unique=False)
    op.create_index('ix_invitations_code', 'invitations', ['code'], unique=True)


def downgrade() -> None:
    """
    Remove invitation system.
    WARNING: This will delete all invitation data!
    """
    # Drop invitations table
    op.drop_index('ix_invitations_code', table_name='invitations')
    op.drop_index('ix_invitations_id', table_name='invitations')
    op.drop_table('invitations')
    
    # Remove columns from users table
    op.drop_constraint('fk_users_invited_by_user_id', 'users', type_='foreignkey')
    op.drop_column('users', 'invited_by_user_id')
    op.drop_column('users', 'invitations_sent')
