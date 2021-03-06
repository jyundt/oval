"""Update Racer and Race models to include aca_member and points_race respectively.

Revision ID: e8ae58376633
Revises: 5794d34e6b61
Create Date: 2016-05-26 14:27:14.925490

"""

# revision identifiers, used by Alembic.
revision = 'e8ae58376633'
down_revision = '5794d34e6b61'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('race', sa.Column('points_race', sa.Boolean(), nullable=True))
    op.add_column('racer', sa.Column('aca_member', sa.Boolean(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('racer', 'aca_member')
    op.drop_column('race', 'points_race')
    ### end Alembic commands ###
