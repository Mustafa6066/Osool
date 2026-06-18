"""Backfill one PropertyPriceSnapshot anchor per existing unit

Revision ID: 038_backfill_property_price_snapshot
Revises: 037_add_forecast_history_tables
Create Date: 2026-06-18

property_price_snapshot (migration 031) has existed but was never written by
the ingestion pipeline, so it is empty. From this deploy the repository writes
a snapshot whenever a price changes (forward accrual). This migration seeds a
single ANCHOR observation per existing unit at Property.created_at so each unit
has a baseline.

Honest caveat: one point per unit is n=1 and contributes nothing to a trend
(Theil-Sen needs >=2 distinct times) — it only becomes useful once forward
accrual adds later observations. Idempotent via NOT EXISTS guard.
"""
from alembic import op


revision = "038_backfill_property_price_snapshot"
down_revision = "037_add_forecast_history_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO property_price_snapshot
            (property_id, observed_at, price_egp, price_per_sqm,
             developer_price, resale_price, source, scrape_run_id)
        SELECT
            p.id,
            COALESCE(p.created_at, NOW()),
            p.price,
            p.price_per_sqm,
            p.developer_price,
            p.resale_price,
            'backfill',
            NULL
        FROM properties p
        WHERE p.price IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM property_price_snapshot s
               WHERE s.property_id = p.id
          );
    """)


def downgrade() -> None:
    # Remove only the rows this migration created.
    op.execute("DELETE FROM property_price_snapshot WHERE source = 'backfill';")
