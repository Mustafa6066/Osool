"""Merge zero-token property branch with main migration chain

Revision ID: 026_merge_zero_token_branch
Revises: 014_add_zero_token_fields, 025_add_subscription_tier
Create Date: 2026-05-10
"""


revision = "026_merge_zero_token_branch"
down_revision = ("014_add_zero_token_fields", "025_add_subscription_tier")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass