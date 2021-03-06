"""Changing a cascading delete for AdminRole

Revision ID: 2072ab37f5a8
Revises: 561431f51d19
Create Date: 2016-04-19 13:32:35.503437

"""

# revision identifiers, used by Alembic.
revision = '2072ab37f5a8'
down_revision = '561431f51d19'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(u'admin_role_role_id_fkey', 'admin_role', type_='foreignkey')
    op.drop_constraint(u'admin_role_admin_id_fkey', 'admin_role', type_='foreignkey')
    op.create_foreign_key(None, 'admin_role', 'admin', ['admin_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'admin_role', 'role', ['role_id'], ['id'], ondelete='CASCADE')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'admin_role', type_='foreignkey')
    op.drop_constraint(None, 'admin_role', type_='foreignkey')
    op.create_foreign_key(u'admin_role_admin_id_fkey', 'admin_role', 'admin', ['admin_id'], ['id'])
    op.create_foreign_key(u'admin_role_role_id_fkey', 'admin_role', 'role', ['role_id'], ['id'])
    ### end Alembic commands ###
