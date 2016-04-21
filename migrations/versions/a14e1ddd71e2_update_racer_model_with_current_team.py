"""Update Racer model with current_team

Revision ID: a14e1ddd71e2
Revises: c52b17f09a01
Create Date: 2016-04-21 10:44:34.991305

"""

# revision identifiers, used by Alembic.
revision = 'a14e1ddd71e2'
down_revision = 'c52b17f09a01'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('racer', sa.Column('current_team', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'racer', 'team', ['current_team'], ['id'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'racer', type_='foreignkey')
    op.drop_column('racer', 'current_team')
    ### end Alembic commands ###