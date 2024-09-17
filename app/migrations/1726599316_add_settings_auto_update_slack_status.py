"""Add settings.auto_update_slack_status

Revision ID: 1726599316
Revises: 1726597351
Create Date: 2024-09-17 18:55:16.766024

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1726599316"
down_revision: Union[str, None] = "1726597351"
branch_labels: Union[str, Sequence[str], None] = ()
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("settings", sa.Column("auto_update_slack_status", sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("settings", "auto_update_slack_status")
    # ### end Alembic commands ###