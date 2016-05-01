"""Add strava url and last_fetch to Racer.

Revision ID: dc435d7f9239
Revises: 0e0c69ae4a91
Create Date: 2016-04-29 15:58:17.418842

"""

# revision identifiers, used by Alembic.
revision = 'dc435d7f9239'
down_revision = '0e0c69ae4a91'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('racer', sa.Column('strava_profile_last_fetch', sa.DateTime(timezone=True), nullable=True))
    op.add_column('racer', sa.Column('strava_profile_url', sa.String(length=200), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('racer', 'strava_profile_url')
    op.drop_column('racer', 'strava_profile_last_fetch')
    ### end Alembic commands ###