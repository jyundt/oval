"""Add Race Class color to schema.

Revision ID: d6015ee1d632
Revises: 628b5fe65b72
Create Date: 2016-04-27 15:40:03.521531

"""

# revision identifiers, used by Alembic.
revision = 'd6015ee1d632'
down_revision = '628b5fe65b72'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('race_class', sa.Column('color', sa.String(length=8), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('race_class', 'color')
    ### end Alembic commands ###
