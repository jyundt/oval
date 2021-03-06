"""add picnic_race boolean

Revision ID: 47f8e5a2a153
Revises: 5f094bf547ed
Create Date: 2017-07-06 18:31:47.178292

"""

# revision identifiers, used by Alembic.
revision = '47f8e5a2a153'
down_revision = '5f094bf547ed'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('race', sa.Column('picnic_race', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('race', 'picnic_race')
    # ### end Alembic commands ###
