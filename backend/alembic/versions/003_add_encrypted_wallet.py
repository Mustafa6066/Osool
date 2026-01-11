"""Add encrypted_private_key to User model

Revision ID: 003_add_encrypted_wallet
Revises: 002_add_kyc_fields
Create Date: 2026-01-12

Phase 1: Security Hardening - Encrypted Wallet Storage
Production Readiness: Critical security fix for custodial wallet management
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_encrypted_wallet'
down_revision = '002_add_kyc_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add encrypted_private_key column to users table.

    Security Implementation:
    - Stores Fernet-encrypted (AES-128-CBC) private keys
    - Nullable to support existing users and non-custodial (wallet-only) accounts
    - Encryption key stored in WALLET_ENCRYPTION_KEY environment variable

    Note: Existing users without wallets will have NULL encrypted_private_key.
    New custodial wallet creation will populate this field with encrypted data.
    """
    op.add_column('users', sa.Column('encrypted_private_key', sa.Text(), nullable=True))


def downgrade() -> None:
    """
    Remove encrypted_private_key column.

    WARNING: This will permanently delete all stored encrypted private keys!
    Ensure you have backups before running this downgrade.
    """
    op.drop_column('users', 'encrypted_private_key')
