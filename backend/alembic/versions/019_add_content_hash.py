"""Add content_hash to properties for differential upsert

Revision ID: 019_add_content_hash
Revises: 018_marketing_materials
Create Date: 2026-03-17

Adds:
- properties.content_hash VARCHAR(64)  — SHA256 of core mutable attributes,
  used by the new ingestion pipeline to skip DB writes and embedding regeneration
  when property data hasn't changed between scrape runs.
- ix_properties_content_hash index for fast lookup
- Partial unique constraint on nawy_url (WHERE nawy_url IS NOT NULL) required
  for INSERT ... ON CONFLICT (nawy_url) in repository.py bulk upsert.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = "019_add_content_hash"
down_revision = "018_marketing_materials"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add the content_hash column
    op.add_column(
        "properties",
        sa.Column("content_hash", sa.String(64), nullable=True),
    )

    # 2. Index for fast hash lookup (O(1) on equality checks in upsert)
    op.create_index(
        "ix_properties_content_hash",
        "properties",
        ["content_hash"],
    )

    # 3. Partial unique index on nawy_url (NULL-safe, supports ON CONFLICT)
    #    Properties ingested before the nawy pipeline may have NULL nawy_url —
    #    the partial index allows those rows to coexist without uniqueness conflicts.
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_properties_nawy_url
        ON properties (nawy_url)
        WHERE nawy_url IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_properties_nawy_url")
    op.drop_index("ix_properties_content_hash", table_name="properties")
    op.drop_column("properties", "content_hash")
