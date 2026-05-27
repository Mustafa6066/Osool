"""Add flag columns to chat_messages so users can report bad AI answers
and admins can escalate them to support tickets.

Revision ID: 035_add_chat_message_flags
Revises: 034_add_hnsw_embedding_index
Create Date: 2026-05-27

A user reading an AI answer should be able to flag it (wrong price, bad
advice, hallucinated property, offensive content). The admin dashboard
should then see those flags and, if the issue is real, convert the
flagged answer into a support ticket so it gets tracked through
resolution like any other ticket.

This migration adds the minimal columns needed to track that lifecycle
on the existing chat_messages table — no new table. The escalation step
creates a real row in the tickets table (with a ticket_id back-pointer
here so the admin can jump between the two views).

Columns added:
    flagged             BOOL DEFAULT FALSE   — set true when user reports
    flag_reason         TEXT NULL            — free-text reason from user
    flag_category       VARCHAR(50) NULL     — one of:
        wrong_price, bad_advice, hallucination, offensive, other
    flagged_at          TIMESTAMPTZ NULL     — when user flagged
    flagged_by_user_id  INT NULL FK users.id — who flagged (NULL = anon)
    escalated_ticket_id INT NULL FK tickets.id — admin escalated → ticket

Idempotent. Partial index on flagged=true for the admin "show flagged"
view since the vast majority of messages will never be flagged.
"""
from alembic import op


revision = "035_add_chat_message_flags"
down_revision = "034_add_hnsw_embedding_index"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE chat_messages
            ADD COLUMN IF NOT EXISTS flagged BOOLEAN NOT NULL DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS flag_reason TEXT NULL,
            ADD COLUMN IF NOT EXISTS flag_category VARCHAR(50) NULL,
            ADD COLUMN IF NOT EXISTS flagged_at TIMESTAMPTZ NULL,
            ADD COLUMN IF NOT EXISTS flagged_by_user_id INTEGER NULL
                REFERENCES users(id) ON DELETE SET NULL,
            ADD COLUMN IF NOT EXISTS escalated_ticket_id INTEGER NULL
                REFERENCES tickets(id) ON DELETE SET NULL
        """
    )

    # Partial index — only the flagged rows are interesting for the admin
    # view. Keeps the index tiny.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chat_messages_flagged_partial
        ON chat_messages (flagged_at DESC, id DESC)
        WHERE flagged = TRUE
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_chat_messages_flagged_partial")
    op.execute(
        """
        ALTER TABLE chat_messages
            DROP COLUMN IF EXISTS escalated_ticket_id,
            DROP COLUMN IF EXISTS flagged_by_user_id,
            DROP COLUMN IF EXISTS flagged_at,
            DROP COLUMN IF EXISTS flag_category,
            DROP COLUMN IF EXISTS flag_reason,
            DROP COLUMN IF EXISTS flagged
        """
    )
