"""sync solicitation model changes

Revision ID: 9e5ad45add14
Revises: 242f6fe44b80
Create Date: 2026-11-06 10:25:01.964305

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9e5ad45add14'
down_revision: Union[str, Sequence[str], None] = '242f6fe44b80'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adds solicitation source identifiers and allows missing metadata"""
    op.add_column(
        "solicitations",
        sa.Column("source_record_id", sa.Text(), nullable=True),
    )

    op.alter_column(
        "solicitations",
        "agency",
        existing_type=sa.Text(),
        nullable=True,
    )

    op.alter_column(
        "solicitations",
        "source_url",
        existing_type=sa.Text(),
        nullable=True,
    )

    op.create_unique_constraint(
        "uq_solicitations_source_record_id",
        "solicitations",
        ["source", "source_record_id"],
    )


def downgrade() -> None:
    """Reverses solicitations schema changes."""
    op.drop_constraint(
        "uq_solicitations_source_record_id",
        "solicitations",
        type_="unique",
    )

    op.alter_column(
        "solicitations",
        "source_url",
        existing_type=sa.Text(),
        nullable=False,
    )

    op.alter_column(
        "solicitations",
        "agency",
        existing_type=sa.Text(),
        nullable=False,
    )

    op.drop_column("solicitations", "source_record_id")