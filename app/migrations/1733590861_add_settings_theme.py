"""Add settings.theme

Revision ID: 1733590861
Revises: 1726779728
Create Date: 2024-12-07 17:01:01.366851

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1733590861"
down_revision: Union[str, None] = "1726779728"
branch_labels: Union[str, Sequence[str], None] = ()
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("settings", sa.Column("theme", sa.String(length=20), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("settings", "theme")
    # ### end Alembic commands ###
