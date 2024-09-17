"""Add UserToSlackToken table

Revision ID: 1726597351
Revises: 
Create Date: 2024-09-17 18:22:31.625463

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1726597351"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = ("default",)
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "user_to_slack_token",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("slack_token", sa.String(length=255), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_user_to_slack_token_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_to_slack_token")),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("user_to_slack_token")
    # ### end Alembic commands ###