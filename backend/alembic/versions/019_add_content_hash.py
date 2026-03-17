"""Add content_hash to properties for differential upsert

Revision ID: 019_add_content_hash
Revises: 018_marketing_materials
Create Date: 2026-03-17

Adds:
- properties.content_hash VARCHAR(64)  — SHA256 of core mutable attributes,
  used by the new ingestion pipeline to skip DB writes and embedding regeneration
  when property data hasn't changed between scrape runs.
- ix_properties_content_hash index for fast lookup
- Partial unique index on nawy_url (WHERE nawy_url IS NOT NULL) required
  for INSERT ... ON CONFLICT (nawy_url) in repository.py bulk upsert.

Safety: deduplicates existing nawy_url rows BEFORE creating the unique index
so this migration is safe to run against production data with duplicates.
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

    # 3. Deduplicate nawy_url values BEFORE creating the unique index.
    #    The old scraper had no uniqueness guarantee on nawy_url, so production
    #    data may have multiple rows sharing the same URL.
    #    Strategy: keep the row with the highest id (most recently inserted)
    #    for each duplicate nawy_url, delete the rest.
    op.execute(
        """
        DELETE FROM properties
        WHERE id IN (
            SELECT id FROM (
                SELECT id,
                       ROW_NUMBER() OVER (
                           PARTITION BY nawy_url
                           ORDER BY id DESC
                       ) AS rn
                FROM properties
                WHERE nawy_url IS NOT NULL
            ) ranked
            WHERE rn > 1
        )
        """
    )

    # 4. Partial unique index on nawy_url (NULL-safe, supports ON CONFLICT).
    #    NULL nawy_url rows (legacy data) are excluded from the constraint so
    #    they can coexist without violating uniqueness.
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
