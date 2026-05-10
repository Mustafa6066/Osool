"""Add hallucination_flags table (Token-Guard inspired verifier)

Revision ID: 024_hallucination_flags
Revises: 023_add_hnsw_and_fts_indexes
Create Date: 2026-04-22

Stores per-claim hallucination flags produced by backend/app/ai_engine/verifier.py.
Indexed on (agent_name, claim_text) to enable weekly TF-IDF + KMeans clustering
of recurring hallucination patterns.
"""

from alembic import op
import sqlalchemy as sa


revision = "024_hallucination_flags"
down_revision = "023_add_hnsw_and_fts_indexes"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "hallucination_flags",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("agent_name", sa.String(length=64), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("query", sa.Text(), nullable=True),
        sa.Column("response_text", sa.Text(), nullable=False),
        sa.Column("claim_text", sa.String(length=500), nullable=False),
        sa.Column("claim_type", sa.String(length=32), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("evidence_source", sa.String(length=128), nullable=True),
        sa.Column("severity", sa.String(length=16), nullable=False, server_default="medium"),
        sa.Column("verifier_model", sa.String(length=128), nullable=True),
        sa.Column("verifier_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_hallucination_flags_agent_name",
        "hallucination_flags",
        ["agent_name"],
    )
    op.create_index(
        "ix_hallucination_flags_session_id",
        "hallucination_flags",
        ["session_id"],
    )
    op.create_index(
        "ix_hallucination_flags_user_id",
        "hallucination_flags",
        ["user_id"],
    )
    op.create_index(
        "ix_hallucination_flags_claim_text",
        "hallucination_flags",
        ["claim_text"],
    )
    op.create_index(
        "ix_hallucination_flags_claim_type",
        "hallucination_flags",
        ["claim_type"],
    )
    op.create_index(
        "ix_hallucination_flags_severity",
        "hallucination_flags",
        ["severity"],
    )
    op.create_index(
        "ix_hallucination_flags_created_at",
        "hallucination_flags",
        ["created_at"],
    )
    # Composite index powering the weekly clustering job
    op.create_index(
        "ix_hallucination_flags_agent_claim",
        "hallucination_flags",
        ["agent_name", "claim_text"],
    )


def downgrade():
    op.drop_index("ix_hallucination_flags_agent_claim", table_name="hallucination_flags")
    op.drop_index("ix_hallucination_flags_created_at", table_name="hallucination_flags")
    op.drop_index("ix_hallucination_flags_severity", table_name="hallucination_flags")
    op.drop_index("ix_hallucination_flags_claim_type", table_name="hallucination_flags")
    op.drop_index("ix_hallucination_flags_claim_text", table_name="hallucination_flags")
    op.drop_index("ix_hallucination_flags_user_id", table_name="hallucination_flags")
    op.drop_index("ix_hallucination_flags_session_id", table_name="hallucination_flags")
    op.drop_index("ix_hallucination_flags_agent_name", table_name="hallucination_flags")
    op.drop_table("hallucination_flags")
