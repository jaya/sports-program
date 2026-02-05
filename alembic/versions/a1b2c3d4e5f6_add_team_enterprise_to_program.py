"""Add team_id and enterprise_id to Program

Revision ID: a1b2c3d4e5f6
Revises: f49de551a508
Create Date: 2026-01-29 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "f49de551a508"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("programs", sa.Column("team_id", sa.String(), nullable=True))
    op.add_column("programs", sa.Column("enterprise_id", sa.String(), nullable=True))
    op.create_index(op.f("ix_programs_team_id"), "programs", ["team_id"], unique=False)
    op.create_index(
        op.f("ix_programs_enterprise_id"), "programs", ["enterprise_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_programs_enterprise_id"), table_name="programs")
    op.drop_index(op.f("ix_programs_team_id"), table_name="programs")
    op.drop_column("programs", "enterprise_id")
    op.drop_column("programs", "team_id")
