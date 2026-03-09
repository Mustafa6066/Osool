"""Add geopolitical events table

Revision ID: 014_add_geopolitical_events
Revises: 013_add_ticketing_system
Create Date: 2026-03-09

Adds:
- geopolitical_events table for storing macro-economic and geopolitical
  events that impact Egyptian real estate investment decisions.
  Consumed by the GeopoliticalLayer in the AI engine.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '014_add_geopolitical_events'
down_revision = '013_add_ticketing_system'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create geopolitical_events table (idempotent)."""

    op.execute("""
        CREATE TABLE IF NOT EXISTS geopolitical_events (
            id SERIAL PRIMARY KEY,
            title VARCHAR(300) NOT NULL,
            summary TEXT NOT NULL,
            source VARCHAR(200),
            source_url TEXT,
            event_date TIMESTAMPTZ NOT NULL,
            category VARCHAR(50) NOT NULL,
            region VARCHAR(50) NOT NULL DEFAULT 'middle_east',
            impact_level VARCHAR(20) NOT NULL,
            impact_tags TEXT,
            real_estate_impact TEXT,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            expires_at TIMESTAMPTZ
        )
    """)

    # Indexes for efficient querying by the AI layer
    op.execute("CREATE INDEX IF NOT EXISTS ix_geopolitical_events_event_date ON geopolitical_events(event_date DESC)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_geopolitical_events_category ON geopolitical_events(category)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_geopolitical_events_impact_level ON geopolitical_events(impact_level)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_geopolitical_events_is_active ON geopolitical_events(is_active)")


def downgrade() -> None:
    """Drop geopolitical_events table."""
    op.execute("DROP TABLE IF EXISTS geopolitical_events CASCADE")
