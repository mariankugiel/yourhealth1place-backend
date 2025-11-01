"""Remove sender_id and sender_type from messages table

Revision ID: remove_sender_fields
Revises: remove_contact_fields
Create Date: 2025-01-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_sender_fields'
down_revision = 'remove_contact_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Check if columns exist before dropping them
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('messages')]
    
    # Remove sender_type field if it exists
    sender_fields = ['sender_type']
    
    for field in sender_fields:
        if field in columns:
            print(f"Dropping column: {field}")
            op.drop_column('messages', field)
        else:
            print(f"Column {field} does not exist, skipping...")
    
    # Keep sender_id foreign key constraint - we're only removing sender_type


def downgrade():
    # Check if columns exist before adding them back
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('messages')]
    
    # Add back sender_type field (only if it doesn't exist)
    if 'sender_type' not in columns:
        print("Adding column: sender_type")
        op.add_column('messages', sa.Column('sender_type', sa.String(length=50), nullable=True))
