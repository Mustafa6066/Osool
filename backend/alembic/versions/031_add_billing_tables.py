"""Add subscriptions + paid_reports tables; type non-property transactions

Revision ID: 031_add_billing_tables
Revises: 030_add_property_price_events
Create Date: 2026-06-11

Monetization wiring:
- transactions.transaction_type (property | subscription | report),
  existing rows backfilled to 'property' via server default
- transactions.property_id becomes nullable (subscriptions/reports have none)
- subscriptions: Osool Pro billing source of truth (periods, renewals)
- paid_reports: one-time purchased AI deliverables
"""
from alembic import op


revision = "031_add_billing_tables"
down_revision = "030_add_property_price_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE transactions
                ADD COLUMN transaction_type VARCHAR(20) NOT NULL DEFAULT 'property';
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)
    op.execute("ALTER TABLE transactions ALTER COLUMN property_id DROP NOT NULL;")

    op.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            plan VARCHAR(30) NOT NULL DEFAULT 'pro_monthly',
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            amount_egp DOUBLE PRECISION NOT NULL,
            current_period_start TIMESTAMPTZ,
            current_period_end TIMESTAMPTZ,
            paymob_order_id VARCHAR,
            transaction_id INTEGER REFERENCES transactions(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_subscriptions_user_id ON subscriptions (user_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_subscriptions_status ON subscriptions (status);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_subscriptions_period_end ON subscriptions (current_period_end);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_subscriptions_paymob_order_id ON subscriptions (paymob_order_id);")

    op.execute("""
        CREATE TABLE IF NOT EXISTS paid_reports (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            report_type VARCHAR(30) NOT NULL DEFAULT 'valuation',
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            input_params_json TEXT,
            content_json TEXT,
            pdf_url TEXT,
            amount_egp DOUBLE PRECISION NOT NULL,
            paymob_order_id VARCHAR,
            transaction_id INTEGER REFERENCES transactions(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            delivered_at TIMESTAMPTZ
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_paid_reports_user_id ON paid_reports (user_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_paid_reports_status ON paid_reports (status);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_paid_reports_paymob_order_id ON paid_reports (paymob_order_id);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS paid_reports;")
    op.execute("DROP TABLE IF EXISTS subscriptions;")
    op.execute("ALTER TABLE transactions DROP COLUMN IF EXISTS transaction_type;")
    # property_id NOT NULL is not restored: legacy rows may legitimately be NULL now
