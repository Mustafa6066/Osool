"""Re-backfill developer_price/resale_price split for rows inserted since 027

Revision ID: 036_backfill_dev_resale_split
Revises: 035_add_chat_message_flags
Create Date: 2026-06-15

Migration 027 added developer_price/resale_price and backfilled them ONCE from
`price` grouped by `sale_type`. Every property scraped between then and now was
written with NULL split columns (the ingestion `_build_row` did not populate
them). The free-path comparison/best-price engine reads these columns, so the
split must be kept complete.

From this deploy forward, `ingestion.repository._build_row` derives the split at
write time. This migration closes the historical gap idempotently: it only
touches rows whose split is still NULL, so it is safe to re-run.
"""
from alembic import op


revision = "036_backfill_dev_resale_split"
down_revision = "035_add_chat_message_flags"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Primary-market pricing — Developer + Nawy Now roll into developer_price.
    op.execute("""
        UPDATE properties
           SET developer_price = price
         WHERE sale_type IN ('Developer', 'Nawy Now')
           AND developer_price IS NULL
           AND price IS NOT NULL;
    """)
    # Secondary-market pricing.
    op.execute("""
        UPDATE properties
           SET resale_price = price
         WHERE sale_type = 'Resale'
           AND resale_price IS NULL
           AND price IS NOT NULL;
    """)


def downgrade() -> None:
    # Non-destructive backfill — nothing to undo. (Reverting would blank out
    # legitimately-scraped split values written by _build_row.)
    pass
