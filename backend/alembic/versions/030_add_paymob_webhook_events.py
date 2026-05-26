"""Add paymob_webhook_events table for idempotency

Revision ID: 030_add_paymob_webhook_events
Revises: 029_add_missing_compound_and_deal_cta
Create Date: 2026-05-26

Audit fix A7: Paymob retries webhooks on timeout/5xx. Without an idempotency
guard, a retry can flip transaction state, create duplicate portfolio
entries, and re-trigger property-reservation side effects.

paymob_webhook_events records every event we've seen by paymob_transaction_id.
The webhook handler INSERTs first, and only proceeds with side effects when
the insert succeeds (i.e. this is the first delivery).
"""
from alembic import op


revision = "030_add_paymob_webhook_events"
down_revision = "029_add_missing_compound_and_deal_cta"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS paymob_webhook_events (
            paymob_transaction_id VARCHAR(64) PRIMARY KEY,
            paymob_order_id VARCHAR(64),
            outcome VARCHAR(32) NOT NULL,
            received_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_paymob_webhook_events_order_id
            ON paymob_webhook_events (paymob_order_id);
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_paymob_webhook_events_order_id;")
    op.execute("DROP TABLE IF EXISTS paymob_webhook_events;")
