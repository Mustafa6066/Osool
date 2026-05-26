"""Extend users table for tiered subscription access

Revision ID: 032_subscription_tier_extensions
Revises: 031_negotiation_constants_and_price_snapshot
Create Date: 2026-05-26

v1 buyer haggle engine — adds the columns the subscription_engine needs to
resolve per-user, per-compound access:

* subscription_expires_at — when the current tier ends (NULL = no expiry, legacy)
* subscription_auto_renew — for premium_monthly, whether the 30-day pass auto-renews
* unlocked_compound_id   — canonical compound name unlocked by the EGP 99 SKU

subscription_tier values used by v1 (backwards-compatible):

* 'free' (default)          — no premium access
* 'single_compound'         — EGP 99 SKU; unlocked_compound_id + expires_at set
* 'premium_monthly'         — EGP 299/mo; expires_at + auto_renew set
* 'premium' (legacy)        — pre-v1 premium; treated as unlimited, no expiry
* 'admin'                   — full access, no expiry

Idempotent: ADD COLUMN IF NOT EXISTS pattern matches migration 029 style.
"""
from alembic import op


revision = "032_subscription_tier_extensions"
down_revision = "031_negotiation_constants_and_price_snapshot"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE users
                ADD COLUMN subscription_expires_at TIMESTAMPTZ;
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            ALTER TABLE users
                ADD COLUMN subscription_auto_renew BOOLEAN NOT NULL DEFAULT FALSE;
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            ALTER TABLE users
                ADD COLUMN unlocked_compound_id VARCHAR(256);
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$;
    """)

    # Index for the auto-renew cron (will scan users where expires_at < now()
    # AND auto_renew = true). Partial index keeps it tiny.
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_users_auto_renew_due
            ON users (subscription_expires_at)
            WHERE subscription_auto_renew = TRUE;
    """)

    # Index for the daily expiry sweep (find tiers to downgrade)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_users_subscription_expires
            ON users (subscription_expires_at)
            WHERE subscription_expires_at IS NOT NULL;
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_users_subscription_expires;")
    op.execute("DROP INDEX IF EXISTS ix_users_auto_renew_due;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS unlocked_compound_id;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS subscription_auto_renew;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS subscription_expires_at;")
