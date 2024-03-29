"""Add user.is_admin

Revision ID: 284a39dbc7ab
Revises: 382a30f9ca44
Create Date: 2023-07-01 17:02:34.270077

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "284a39dbc7ab"
down_revision = "382a30f9ca44"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("is_admin", sa.Boolean()))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("is_admin")

    # ### end Alembic commands ###
