"""Fix uq_properties_nawy_url to also exclude empty-string nawy_url

Revision ID: 020_fix_nawy_url_empty_string
Revises: 019_add_content_hash
Create Date: 2026-03-17

Problem:
  The partial unique index from migration 019 uses:
      WHERE nawy_url IS NOT NULL
  PostgreSQL treats '' (empty string) as NOT NULL, so multiple rows with
  nawy_url='' all map to the same index key → UniqueViolationError on insert.

Fix:
  1. Null-out existing empty-string nawy_url values (they have no real URL,
     so NULL is semantically correct and excluded from the unique index).
  2. Drop the old partial index.
  3. Recreate it with:  WHERE nawy_url IS NOT NULL AND nawy_url <> ''
  4. Update the ON CONFLICT index condition in the repository is handled
     automatically since the index definition changes.

Fully idempotent.
"""

from alembic import op

revision = "020_fix_nawy_url_empty_string"
down_revision = "019_add_content_hash"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Convert empty-string nawy_url to NULL (semantically correct — no URL).
    #    This also collapses duplicates: multiple '' rows become multiple NULLs,
    #    which are not subject to the unique constraint.
    op.execute(
        "UPDATE properties SET nawy_url = NULL WHERE nawy_url = ''"
    )

    # 2. Drop the old index that only excluded NULLs.
    op.execute("DROP INDEX IF EXISTS uq_properties_nawy_url")

    # 3. Recreate with both NULL and empty-string excluded.
    #    Using IF NOT EXISTS for idempotency.
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_properties_nawy_url
        ON properties (nawy_url)
        WHERE nawy_url IS NOT NULL AND nawy_url <> ''
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_properties_nawy_url")
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_properties_nawy_url
        ON properties (nawy_url)
        WHERE nawy_url IS NOT NULL
        """
    )
