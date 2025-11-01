"""add role column to users table

Revision ID: add_role_to_users_table
Revises: remove_redundant_message_fields
Create Date: 2024-01-20 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_role_to_users_table'
down_revision = 'remove_redundant_message_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum type for user roles
    role_enum = postgresql.ENUM('patient', 'doctor', 'admin', name='userrole')
    role_enum.create(op.get_bind())
    
    # Add role column to users table
    op.add_column('users', sa.Column('role', role_enum, nullable=False, server_default='patient'))
    
    # Create index on role column for better query performance
    op.create_index('idx_users_role', 'users', ['role'])


def downgrade():
    # Drop index
    op.drop_index('idx_users_role', table_name='users')
    
    # Drop role column
    op.drop_column('users', 'role')
    
    # Drop enum type
    op.execute('DROP TYPE IF EXISTS userrole')
