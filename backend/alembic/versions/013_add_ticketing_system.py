"""Add ticketing system

Revision ID: 013_add_ticketing_system
Revises: 012_remove_blockchain_tables
Create Date: 2026-03-09

Adds:
- tickets table (support tickets created by users)
- ticket_replies table (threaded replies on tickets)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '013_add_ticketing_system'
down_revision = '012_remove_blockchain_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create ticketing system tables (idempotent)."""

    # 1. tickets
    op.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            subject VARCHAR(200) NOT NULL,
            description TEXT NOT NULL,
            category VARCHAR(50) NOT NULL DEFAULT 'general',
            priority VARCHAR(20) NOT NULL DEFAULT 'medium',
            status VARCHAR(20) NOT NULL DEFAULT 'open',
            assigned_to INTEGER REFERENCES users(id),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            closed_at TIMESTAMPTZ
        )
    """)

    # Indexes for tickets
    op.execute("CREATE INDEX IF NOT EXISTS ix_tickets_user_id ON tickets(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tickets_status ON tickets(status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tickets_created_at ON tickets(created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tickets_assigned_to ON tickets(assigned_to)")

    # 2. ticket_replies
    op.execute("""
        CREATE TABLE IF NOT EXISTS ticket_replies (
            id SERIAL PRIMARY KEY,
            ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id),
            content TEXT NOT NULL,
            is_admin_reply BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Indexes for ticket_replies
    op.execute("CREATE INDEX IF NOT EXISTS ix_ticket_replies_ticket_id ON ticket_replies(ticket_id)")


def downgrade() -> None:
    """Remove ticketing system tables."""
    op.execute("DROP TABLE IF EXISTS ticket_replies CASCADE")
    op.execute("DROP TABLE IF EXISTS tickets CASCADE")
