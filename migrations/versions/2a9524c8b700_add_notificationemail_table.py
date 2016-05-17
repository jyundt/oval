"""Add NotificationEmail table.

Revision ID: 2a9524c8b700
Revises: 51d251f9b887
Create Date: 2016-05-15 07:22:04.529845

"""

# revision identifiers, used by Alembic.
revision = '2a9524c8b700'
down_revision = '51d251f9b887'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('notificationemail',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=50), nullable=False),
    sa.Column('description', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('notificationemail')
    ### end Alembic commands ###
