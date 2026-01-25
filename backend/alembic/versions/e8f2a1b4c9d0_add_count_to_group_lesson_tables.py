"""add count to group-lesson tables

Revision ID: e8f2a1b4c9d0
Revises: d510a55d15d3
Create Date: 2026-01-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e8f2a1b4c9d0"
down_revision: Union[str, Sequence[str], None] = "d510a55d15d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add count column to class_group_lessons and study_group_lessons."""
    op.add_column(
        "class_group_lessons",
        sa.Column("count", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "study_group_lessons",
        sa.Column("count", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    """Remove count column from both tables."""
    op.drop_column("class_group_lessons", "count")
    op.drop_column("study_group_lessons", "count")
