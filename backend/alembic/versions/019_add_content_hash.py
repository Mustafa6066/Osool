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

Fully idempotent: every DDL statement uses IF NOT EXISTS / IF EXISTS so the
migration is safe to re-run if a previous attempt failed partway through.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = "019_add_content_hash"
down_revision = "018_marketing_materials"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add content_hash column — idempotent via PostgreSQL ADD COLUMN IF NOT EXISTS
    op.execute(
        "ALTER TABLE properties ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64)"
    )

    # 2. Index for fast hash lookup — idempotent
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_properties_content_hash ON properties (content_hash)"
    )

    # 3. Deduplicate nawy_url values BEFORE creating the unique index.
    #    Keep the row with the highest id (most recently inserted) per duplicate nawy_url.
    #    Safe to re-run: if no duplicates exist, the DELETE is a no-op.
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

    # 4. Partial unique index on nawy_url (NULL-safe).
    #    IF NOT EXISTS makes this idempotent.
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_properties_nawy_url
        ON properties (nawy_url)
        WHERE nawy_url IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_properties_nawy_url")
    op.execute("DROP INDEX IF EXISTS ix_properties_content_hash")
    op.execute("ALTER TABLE properties DROP COLUMN IF EXISTS content_hash")
