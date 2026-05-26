"""Add negotiation_constants and property_price_snapshot tables

Revision ID: 031_negotiation_constants_and_price_snapshot
Revises: 030_add_paymob_webhook_events
Create Date: 2026-05-26

v1 buyer haggle engine — two foundational tables:

* negotiation_constants
  Admin-editable Egyptian negotiation multipliers (cash discount %, broker
  commission %, off-plan discount, scarcity premium, launch fade). Scoped
  global by default with per-developer/area/compound overrides.

* property_price_snapshot
  Unit-level price history. Inserted by the scraper pipeline whenever a
  property's price changes. Powers the 6-month trend chart (premium) and
  enables back-testing of the negotiation_constants calibration.
"""
from alembic import op


revision = "031_negotiation_constants_and_price_snapshot"
down_revision = "030_add_paymob_webhook_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── negotiation_constants ────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS negotiation_constants (
            id BIGSERIAL PRIMARY KEY,
            constant_key VARCHAR(64) NOT NULL,
            scope_type VARCHAR(16) NOT NULL DEFAULT 'global',
            scope_id VARCHAR(128),
            value_min NUMERIC(12, 6) NOT NULL,
            value_max NUMERIC(12, 6) NOT NULL,
            unit VARCHAR(16) NOT NULL,
            notes TEXT,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT negotiation_constants_scope_type_check
                CHECK (scope_type IN ('global', 'developer', 'area', 'compound')),
            CONSTRAINT negotiation_constants_value_range_check
                CHECK (value_max >= value_min)
        );
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_negotiation_constants_key_scope
            ON negotiation_constants (constant_key, scope_type, COALESCE(scope_id, ''));
    """)

    # ── Seed default global ranges ───────────────────────────────────────
    # Defaults are educated starting values; admins recalibrate using
    # property_price_snapshot history and ground-truth closings.
    op.execute("""
        INSERT INTO negotiation_constants
            (constant_key, scope_type, scope_id, value_min, value_max, unit, notes)
        VALUES
            ('cash_discount_pct', 'global', NULL, 0.05, 0.15, 'pct',
                'Discount range for upfront-cash settlement vs payment plan.'),
            ('broker_commission_pct_resale', 'global', NULL, 0.025, 0.025, 'pct',
                'Standard buyer-side broker commission on resale transactions.'),
            ('broker_commission_pct_primary', 'global', NULL, 0.0, 0.0, 'pct',
                'Primary-market sales typically carry no buyer-side broker commission.'),
            ('off_plan_discount_per_year', 'global', NULL, 0.06, 0.06, 'pct',
                'Annual delivery-lag penalty applied to off-plan units (-6%/year wait).'),
            ('scarcity_threshold_units', 'global', NULL, 5, 5, 'units',
                'Inventory level below which scarcity premium activates.'),
            ('scarcity_premium_pct', 'global', NULL, 0.05, 0.05, 'pct',
                'Premium added when available units in compound < threshold.'),
            ('launch_fade_per_month', 'global', NULL, 0.005, 0.015, 'pct',
                'Resale price fade per month after launch peak.'),
            ('confidence_haircut_pct', 'global', NULL, 0.02, 0.02, 'pct',
                'Width reduction per confidence tier drop. High=0, moderate=2%, indicative=4%.'),
            ('payment_plan_npv_enabled', 'global', NULL, 1, 1, 'flag',
                'Use NPV vs cash from valuation_engine for payment-plan markup. 1=enabled.')
        ON CONFLICT DO NOTHING;
    """)

    # ── Seed tier-1 developer overrides (illustrative starting points) ───
    op.execute("""
        INSERT INTO negotiation_constants
            (constant_key, scope_type, scope_id, value_min, value_max, unit, notes)
        VALUES
            ('cash_discount_pct', 'developer', 'emaar-misr', 0.03, 0.08, 'pct',
                'Emaar Misr — tier-1; tighter discount room than market default.'),
            ('cash_discount_pct', 'developer', 'sodic', 0.04, 0.10, 'pct',
                'SODIC — tier-1; moderate discount room.'),
            ('cash_discount_pct', 'developer', 'palm-hills', 0.05, 0.12, 'pct',
                'Palm Hills — moderate flexibility.'),
            ('cash_discount_pct', 'developer', 'hassan-allam', 0.05, 0.12, 'pct',
                'Hassan Allam — moderate flexibility.'),
            ('cash_discount_pct', 'developer', 'ora-developers', 0.04, 0.10, 'pct',
                'ORA Developers — tier-1.')
        ON CONFLICT DO NOTHING;
    """)

    # ── property_price_snapshot ──────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS property_price_snapshot (
            id BIGSERIAL PRIMARY KEY,
            property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
            observed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            price_egp NUMERIC(14, 2) NOT NULL,
            price_per_sqm NUMERIC(12, 2),
            developer_price NUMERIC(14, 2),
            resale_price NUMERIC(14, 2),
            source VARCHAR(64) NOT NULL,
            scrape_run_id VARCHAR(64)
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_price_snapshot_property_observed
            ON property_price_snapshot (property_id, observed_at DESC);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_price_snapshot_observed
            ON property_price_snapshot (observed_at DESC);
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_price_snapshot_observed;")
    op.execute("DROP INDEX IF EXISTS ix_price_snapshot_property_observed;")
    op.execute("DROP TABLE IF EXISTS property_price_snapshot;")
    op.execute("DROP INDEX IF EXISTS ux_negotiation_constants_key_scope;")
    op.execute("DROP TABLE IF EXISTS negotiation_constants;")
