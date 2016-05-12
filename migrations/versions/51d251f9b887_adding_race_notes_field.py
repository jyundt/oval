"""Adding race notes field.

Revision ID: 51d251f9b887
Revises: e316df277b2f
Create Date: 2016-05-12 09:57:20.747773

"""

# revision identifiers, used by Alembic.
revision = '51d251f9b887'
down_revision = 'e316df277b2f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('race', sa.Column('notes', sa.Text(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('race', 'notes')
    ### end Alembic commands ###