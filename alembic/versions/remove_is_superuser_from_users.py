"""remove is_superuser column from users table

Revision ID: remove_is_superuser_from_users
Revises: add_role_to_users_table
Create Date: 2024-01-20 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_is_superuser_from_users'
down_revision = 'add_role_to_users_table'
branch_labels = None
depends_on = None


def upgrade():
    # Remove is_superuser column from users table
    op.drop_column('users', 'is_superuser')


def downgrade():
    # Add back is_superuser column
    op.add_column('users', sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'))
