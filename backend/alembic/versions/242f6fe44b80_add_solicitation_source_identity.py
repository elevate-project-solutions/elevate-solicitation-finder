"""Add solicitation source identity

Revision ID: 242f6fe44b80
Revises: 69d3c5aab5d3
Create Date: 2026-11-05 11:09:05.761622

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '242f6fe44b80'
down_revision: Union[str, Sequence[str], None] = '69d3c5aab5d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
    """Downgrade schema."""
    op.drop_contraint(
        "uq_solicitations_source_record_id",
        "solicitations",
        type="unique",
    )

    op.drop_column("solicitations", "source_record_id")

    op.alter_column(
        "solicitations",
        "agency",
        existing_type=sa.Text(),
        nullable=False,
    )

    op.alter_column(
        "solicitations",
        "source_url",
        existing_type=sa.Text(),
        nullable=False,
    )
