"""Enhance market_indicators table and seed initial data

Revision ID: 007_enhance_market_indicators
Revises: 006_add_invitation_system
Create Date: 2026-02-12

Adds:
- source column to market_indicators table
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
    Enhance market_indicators:
    1. Add source column for data provenance tracking
    2. Seed initial Egyptian market indicators
    """

    # Add source column to market_indicators table
    op.add_column('market_indicators', sa.Column('source', sa.String(200), nullable=True))

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
    Remove enhancements from market_indicators.
    WARNING: This will delete seeded data!
    """
    # Delete seeded data
    op.execute("""
        DELETE FROM market_indicators WHERE key IN (
            'inflation_rate', 'bank_cd_rate', 'property_appreciation',
            'rental_yield_avg', 'gold_appreciation', 'usd_egp_rate',
            'mortgage_rate', 'rent_increase_rate'
        )
    """)

    # Remove source column
    op.drop_column('market_indicators', 'source')
