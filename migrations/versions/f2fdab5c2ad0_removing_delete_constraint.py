"""Removing delete constraint.

Revision ID: f2fdab5c2ad0
Revises: 2072ab37f5a8
Create Date: 2016-04-19 13:50:05.208282

"""

# revision identifiers, used by Alembic.
revision = 'f2fdab5c2ad0'
down_revision = '2072ab37f5a8'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(u'admin_role_admin_id_fkey', 'admin_role', type_='foreignkey')
    op.drop_constraint(u'admin_role_role_id_fkey', 'admin_role', type_='foreignkey')
    op.create_foreign_key(None, 'admin_role', 'role', ['role_id'], ['id'])
    op.create_foreign_key(None, 'admin_role', 'admin', ['admin_id'], ['id'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'admin_role', type_='foreignkey')
    op.drop_constraint(None, 'admin_role', type_='foreignkey')
    op.create_foreign_key(u'admin_role_role_id_fkey', 'admin_role', 'role', ['role_id'], ['id'], ondelete=u'CASCADE')
    op.create_foreign_key(u'admin_role_admin_id_fkey', 'admin_role', 'admin', ['admin_id'], ['id'], ondelete=u'CASCADE')
    ### end Alembic commands ###
