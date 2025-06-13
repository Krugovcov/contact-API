"""Add user_id to contacts

Revision ID: 9a97a61fe92b
Revises: 0e031fe920b6
Create Date: 2025-05-17 08:48:34.638452

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a97a61fe92b'
down_revision: Union[str, None] = '0e031fe920b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('contacts', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_contacts_user_id_users',
        'contacts', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade():
    op.drop_constraint('fk_contacts_user_id_users', 'contacts', type_='foreignkey')
    op.drop_column('contacts', 'user_id')