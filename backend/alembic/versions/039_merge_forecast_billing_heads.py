"""Merge the forecast-history and billing migration heads into one

Revision ID: 039_merge_forecast_billing_heads
Revises: 038_backfill_dev_resale_split, 038_backfill_property_price_snapshot
Create Date: 2026-06-18

The branch carried two divergent Alembic heads:

  * 038_backfill_dev_resale_split          (billing lineage: 036_add_property_price_events
                                            → 037_add_billing_tables → 038_backfill_dev_resale_split)
  * 038_backfill_property_price_snapshot   (forecast lineage: 036_backfill_dev_resale_split
                                            → 037_add_forecast_history_tables
                                            → 038_backfill_property_price_snapshot)

`alembic upgrade head` (singular, run by docker-entrypoint.sh on deploy) errors when
multiple heads exist. This no-op merge revision unifies them so there is a single
head again; `upgrade head` then applies BOTH lineages.
"""
from alembic import op  # noqa: F401


revision = "039_merge_forecast_billing_heads"
down_revision = ("038_backfill_dev_resale_split", "038_backfill_property_price_snapshot")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No schema changes — this revision only reconciles the two heads.
    pass


def downgrade() -> None:
    pass
