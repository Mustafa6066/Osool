"""Create market_indicators table and seed initial data

Revision ID: 007_enhance_market_indicators
Revises: 006_add_invitation_system
Create Date: 2026-02-12

Adds:
- Creates market_indicators table (if not exists)
- Seeds initial Egyptian market economic indicators
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007_enhance_market_indicators'
down_revision = '006_add_invitation_system'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create market_indicators table and seed initial data:
    1. Create table if not exists
    2. Seed initial Egyptian market indicators
    """

    # Create market_indicators table
    op.create_table(
        'market_indicators',
        sa.Column('key', sa.String(100), primary_key=True),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('source', sa.String(200), nullable=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True)
    )

    # Seed initial market indicators for Egyptian real estate market
    # Using raw SQL for data insertion
    op.execute("""
        INSERT INTO market_indicators (key, value, source) VALUES
        ('inflation_rate', 0.136, 'Central Bank of Egypt Feb 2026'),
        ('bank_cd_rate', 0.22, 'CIB/NBE Feb 2026'),
        ('property_appreciation', 0.145, 'Osool Market Research'),
        ('rental_yield_avg', 0.075, 'Osool Analytics'),
        ('gold_appreciation', 0.15, 'COMEX Egypt'),
        ('usd_egp_rate', 50.5, 'Central Bank of Egypt'),
        ('mortgage_rate', 0.12, 'Housing Finance Egypt'),
        ('rent_increase_rate', 0.12, 'Osool Analytics')
        ON CONFLICT (key) DO UPDATE SET
            value = EXCLUDED.value,
            source = EXCLUDED.source
    """)


def downgrade() -> None:
    """
    Remove market_indicators table.
    WARNING: This will delete all market indicator data!
    """
    op.drop_table('market_indicators')
