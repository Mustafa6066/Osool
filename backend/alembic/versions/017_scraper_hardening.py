"""Scraper hardening: stale cleanup, image mirroring, price flags, sentiment

Revision ID: 017_scraper_hardening
Revises: 016_add_missing_dual_engine_columns
Create Date: 2026-03-16

Adds:
- properties.last_scrape_run_id (VARCHAR(36), indexed) — track which scrape run touched each row
- properties.mirrored_image_url (TEXT) — S3/R2 hosted image copy
- properties.price_flag (VARCHAR(50)) — cross-DB validation flags (e.g. 'potential_high_roi')
- geopolitical_events.sentiment_score (FLOAT) — numeric sentiment from -1.0 to +1.0
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "017_scraper_hardening"
down_revision = "016_add_missing_dual_engine_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Properties table — scraper tracking
    op.add_column("properties", sa.Column("last_scrape_run_id", sa.String(36), nullable=True))
    op.add_column("properties", sa.Column("mirrored_image_url", sa.Text(), nullable=True))
    op.add_column("properties", sa.Column("price_flag", sa.String(50), nullable=True))
    op.create_index("ix_properties_last_scrape_run_id", "properties", ["last_scrape_run_id"])

    # Geopolitical events — sentiment scalar
    op.add_column("geopolitical_events", sa.Column("sentiment_score", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("geopolitical_events", "sentiment_score")
    op.drop_index("ix_properties_last_scrape_run_id", table_name="properties")
    op.drop_column("properties", "price_flag")
    op.drop_column("properties", "mirrored_image_url")
    op.drop_column("properties", "last_scrape_run_id")
