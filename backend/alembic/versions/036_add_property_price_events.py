"""Add property_price_events table for per-property price change tracking

Revision ID: 030_add_property_price_events
Revises: 029_add_missing_compound_and_deal_cta
Create Date: 2026-06-11

Captures price movements detected by the differential upsert during scrape
ingestion. Feeds price-drop alerts (saved searches) and market trend pages.
"""
from alembic import op


revision = "030_add_property_price_events"
down_revision = "029_add_missing_compound_and_deal_cta"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS property_price_events (
            id SERIAL PRIMARY KEY,
            property_id INTEGER REFERENCES properties(id),
            nawy_url TEXT NOT NULL,
            old_price DOUBLE PRECISION NOT NULL,
            new_price DOUBLE PRECISION NOT NULL,
            pct_change DOUBLE PRECISION NOT NULL,
            scrape_run_id VARCHAR(36),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_property_price_events_property_id "
        "ON property_price_events (property_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_property_price_events_nawy_url "
        "ON property_price_events (nawy_url);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_property_price_events_created_at "
        "ON property_price_events (created_at);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_property_price_events_scrape_run_id "
        "ON property_price_events (scrape_run_id);"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS property_price_events;")
