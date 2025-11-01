"""remove contact_name, contact_role, contact_avatar, contact_type from conversations table

Revision ID: remove_contact_fields
Revises: remove_is_superuser_from_users
Create Date: 2024-01-20 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_contact_fields'
down_revision = 'remove_is_superuser_from_users'
branch_labels = None
depends_on = None


def upgrade():
    # Check if columns exist before dropping them
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('conversations')]
    
    # Remove contact fields if they exist
    contact_fields = ['contact_name', 'contact_role', 'contact_avatar', 'contact_type']
    
    for field in contact_fields:
        if field in columns:
            print(f"Dropping column: {field}")
            op.drop_column('conversations', field)
        else:
            print(f"Column {field} does not exist, skipping...")


def downgrade():
    # Check if columns exist before adding them back
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('conversations')]
    
    # Add back contact fields (only if they don't exist)
    if 'contact_name' not in columns:
        op.add_column('conversations', sa.Column('contact_name', sa.String(length=255), nullable=True))
    
    if 'contact_role' not in columns:
        op.add_column('conversations', sa.Column('contact_role', sa.String(length=100), nullable=True))
    
    if 'contact_avatar' not in columns:
        op.add_column('conversations', sa.Column('contact_avatar', sa.String(length=500), nullable=True))
    
    if 'contact_type' not in columns:
        op.add_column('conversations', sa.Column('contact_type', sa.String(length=50), nullable=True))
