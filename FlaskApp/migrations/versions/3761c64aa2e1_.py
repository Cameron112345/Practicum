"""empty message

Revision ID: 3761c64aa2e1
Revises: 8e88eda540bc
Create Date: 2023-05-01 17:39:55.229685

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3761c64aa2e1'
down_revision = '8e88eda540bc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('archive', schema=None) as batch_op:
        batch_op.add_column(sa.Column('prefix', sa.String(length=40), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('archive', schema=None) as batch_op:
        batch_op.drop_column('prefix')

    # ### end Alembic commands ###