"""Add initial s3 upload support.

Revision ID: 5f094bf547ed
Revises: 456cc02b1824
Create Date: 2017-05-24 07:54:45.958226

"""

# revision identifiers, used by Alembic.
revision = '5f094bf547ed'
down_revision = '456cc02b1824'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('race_attachment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('key', sa.String(length=32), nullable=True),
    sa.Column('race_id', sa.Integer(), nullable=True),
    sa.Column('description', sa.String(length=200), nullable=False),
    sa.Column('filename', sa.String(length=200), nullable=False),
    sa.Column('mimetype', sa.String(length=64), nullable=False),
    sa.ForeignKeyConstraint(['race_id'], ['race.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('key')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('race_attachment')
    # ### end Alembic commands ###
