"""remove redundant message fields

Revision ID: remove_redundant_message_fields
Revises: create_message_documents_table
Create Date: 2024-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = 'remove_redundant_message_fields'
down_revision = 'create_message_documents_table'
branch_labels = None
depends_on = None


def upgrade():
    # Check if columns exist before dropping them
    connection = op.get_bind()
    
    # Get current table structure
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('messages')]
    
    # Remove redundant sender fields if they exist
    redundant_fields = [
        'sender_name',
        'sender_role', 
        'sender_avatar',
        'recipient_id',
        'recipient_name',
        'recipient_role',
        'recipient_type',
        'recipient_avatar'
    ]
    
    for field in redundant_fields:
        if field in columns:
            print(f"Dropping column: {field}")
            op.drop_column('messages', field)
        else:
            print(f"Column {field} does not exist, skipping...")
    
    # Add any missing indexes for performance
    try:
        op.create_index('idx_messages_conversation_id', 'messages', ['conversation_id'])
    except Exception:
        pass  # Index might already exist
        
    try:
        op.create_index('idx_messages_sender_id', 'messages', ['sender_id'])
    except Exception:
        pass  # Index might already exist
        
    try:
        op.create_index('idx_messages_created_at', 'messages', ['created_at'])
    except Exception:
        pass  # Index might already exist


def downgrade():
    # Check if columns exist before adding them back
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('messages')]
    
    # Add back the redundant fields for rollback (only if they don't exist)
    if 'sender_name' not in columns:
        op.add_column('messages', sa.Column('sender_name', sa.String(length=255), nullable=False, server_default='Unknown'))
    
    if 'sender_role' not in columns:
        op.add_column('messages', sa.Column('sender_role', sa.String(length=100), nullable=False, server_default='Unknown'))
    
    if 'sender_avatar' not in columns:
        op.add_column('messages', sa.Column('sender_avatar', sa.String(length=500), nullable=True))
    
    # Add back recipient fields (only if they don't exist)
    if 'recipient_id' not in columns:
        op.add_column('messages', sa.Column('recipient_id', sa.Integer(), nullable=True))
    
    if 'recipient_name' not in columns:
        op.add_column('messages', sa.Column('recipient_name', sa.String(length=255), nullable=True))
    
    if 'recipient_role' not in columns:
        op.add_column('messages', sa.Column('recipient_role', sa.String(length=100), nullable=True))
    
    if 'recipient_type' not in columns:
        op.add_column('messages', sa.Column('recipient_type', sa.String(length=50), nullable=True))
    
    if 'recipient_avatar' not in columns:
        op.add_column('messages', sa.Column('recipient_avatar', sa.String(length=500), nullable=True))
    
    # Drop the indexes we created
    try:
        op.drop_index('idx_messages_conversation_id', table_name='messages')
    except Exception:
        pass
        
    try:
        op.drop_index('idx_messages_sender_id', table_name='messages')
    except Exception:
        pass
        
    try:
        op.drop_index('idx_messages_created_at', table_name='messages')
    except Exception:
        pass
