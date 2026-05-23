"""add consultation bookings table

Revision ID: 028_add_consultation_bookings
Revises: 027_add_developer_resale_prices_and_free_path_session
Create Date: 2026-05-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "028_add_consultation_bookings"
down_revision: Union[str, None] = "027_add_developer_resale_prices_and_free_path_session"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "consultation_bookings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=True),
        sa.Column("booking_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="scheduled"),
        sa.Column("scheduled_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("assigned_broker_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_consultation_bookings_id"), "consultation_bookings", ["id"], unique=False)
    op.create_index(op.f("ix_consultation_bookings_user_id"), "consultation_bookings", ["user_id"], unique=False)
    op.create_index(op.f("ix_consultation_bookings_property_id"), "consultation_bookings", ["property_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_consultation_bookings_property_id"), table_name="consultation_bookings")
    op.drop_index(op.f("ix_consultation_bookings_user_id"), table_name="consultation_bookings")
    op.drop_index(op.f("ix_consultation_bookings_id"), table_name="consultation_bookings")
    op.drop_table("consultation_bookings")
