"""Remove reservation / anti-double-booking controls

Revision ID: 040_remove_reservation_controls
Revises: 039_merge_forecast_billing_heads
Create Date: 2026-06-18

Drops the reservation-specific tracking column now that the property
reservation / anti-double-booking transaction-control layer has been removed.
Payments (Paymob/Fawry/InstaPay) and viewing analytics are unaffected.

- conversation_analytics.reservation_generated -> dropped
  (the "reserved" conversion path no longer exists; viewing_scheduled stays)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '040_remove_reservation_controls'
down_revision = '039_merge_forecast_billing_heads'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Drop the reservation_generated tracking column."""
    op.execute(
        "ALTER TABLE conversation_analytics DROP COLUMN IF EXISTS reservation_generated;"
    )


def downgrade() -> None:
    """Restore the reservation_generated column (defaults to false)."""
    op.add_column(
        'conversation_analytics',
        sa.Column(
            'reservation_generated',
            sa.Boolean(),
            server_default='false',
            nullable=False,
        ),
    )
