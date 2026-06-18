"""Add developer_price_history and market_indicator_history tables

Revision ID: 037_add_forecast_history_tables
Revises: 036_backfill_dev_resale_split
Create Date: 2026-06-18

Foundation for the scientific price-forecasting engine (price_forecast_engine).

* developer_price_history
  Developer-level historical price/m² series. PriceHistory keys only
  project_id/area_id and never the free-text Property.developer string the
  forecaster pivots on, so this table fills that gap. Seeded from
  analytical_engine's curated 2021–2026 dicts (source='analytical_engine_seed_2026')
  and accumulated forward from monthly PropertyPriceSnapshot aggregates.

* market_indicator_history
  Dated time-series companion to market_indicators (which is latest-value-only).
  Stores a CPI INDEX LEVEL ('cpi_index'), 'inflation_rate', 'egp_per_usd', etc.
  so nominal EGP/m² can be deflated to real terms around the 2022/2024 EGP
  devaluations: real(t) = nominal(t) * cpi(base)/cpi(t).
"""
from alembic import op


revision = "037_add_forecast_history_tables"
down_revision = "036_backfill_dev_resale_split"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── developer_price_history ──────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS developer_price_history (
            id BIGSERIAL PRIMARY KEY,
            developer_name VARCHAR(200) NOT NULL,
            area VARCHAR(120),
            unit_type VARCHAR(40),
            price_per_m2 NUMERIC(12, 2) NOT NULL,
            observed_at TIMESTAMPTZ NOT NULL,
            source VARCHAR(64) NOT NULL,
            citation_url TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_developer_price_history_key
                UNIQUE (developer_name, observed_at, unit_type, source)
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_developer_price_history_dev_observed
            ON developer_price_history (developer_name, observed_at DESC);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_developer_price_history_observed
            ON developer_price_history (observed_at DESC);
    """)

    # ── market_indicator_history ─────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS market_indicator_history (
            id BIGSERIAL PRIMARY KEY,
            key VARCHAR(100) NOT NULL,
            value NUMERIC(18, 6) NOT NULL,
            observed_at TIMESTAMPTZ NOT NULL,
            source VARCHAR(200),
            citation_url TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_market_indicator_history_key_observed
                UNIQUE (key, observed_at)
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_market_indicator_history_key_observed
            ON market_indicator_history (key, observed_at DESC);
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_market_indicator_history_key_observed;")
    op.execute("DROP TABLE IF EXISTS market_indicator_history;")
    op.execute("DROP INDEX IF EXISTS ix_developer_price_history_observed;")
    op.execute("DROP INDEX IF EXISTS ix_developer_price_history_dev_observed;")
    op.execute("DROP TABLE IF EXISTS developer_price_history;")
