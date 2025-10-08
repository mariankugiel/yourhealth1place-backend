"""Create messages system

Revision ID: 0003
Revises: 0002
Create Date: 2025-01-29 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade():
    # Create enums
    message_type_enum = postgresql.ENUM(
        'health_plan_support', 'medication_reminder', 'appointment_reminder', 
        'lab_results', 'doctor_message', 'system_announcement', 
        'prescription_update', 'insurance_update', 'general',
        name='messagetype'
    )
    message_type_enum.create(op.get_bind())

    message_priority_enum = postgresql.ENUM(
        'low', 'normal', 'high', 'urgent',
        name='messagepriority'
    )
    message_priority_enum.create(op.get_bind())

    message_status_enum = postgresql.ENUM(
        'sent', 'delivered', 'read', 'failed',
        name='messagestatus'
    )
    message_status_enum.create(op.get_bind())

    sender_type_enum = postgresql.ENUM(
        'user', 'doctor', 'admin', 'system',
        name='sendertype'
    )
    sender_type_enum.create(op.get_bind())

    # Create conversations table
    op.create_table('conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('contact_id', sa.Integer(), nullable=False),
        sa.Column('contact_name', sa.String(length=255), nullable=False),
        sa.Column('contact_role', sa.String(length=100), nullable=False),
        sa.Column('contact_avatar', sa.String(length=500), nullable=True),
        sa.Column('contact_type', sender_type_enum, nullable=False),
        sa.Column('is_archived', sa.Boolean(), nullable=True),
        sa.Column('is_pinned', sa.Boolean(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_message_time', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['contact_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversations_id'), 'conversations', ['id'], unique=False)

    # Create messages table
    op.create_table('messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('sender_name', sa.String(length=255), nullable=False),
        sa.Column('sender_role', sa.String(length=100), nullable=False),
        sa.Column('sender_type', sender_type_enum, nullable=False),
        sa.Column('sender_avatar', sa.String(length=500), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', message_type_enum, nullable=False),
        sa.Column('priority', message_priority_enum, nullable=False),
        sa.Column('status', message_status_enum, nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_id'), 'messages', ['id'], unique=False)

    # Create message_delivery_logs table
    op.create_table('message_delivery_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('delivery_method', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_message_delivery_logs_id'), 'message_delivery_logs', ['id'], unique=False)

    # Create message_actions table
    op.create_table('message_actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('action_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_message_actions_id'), 'message_actions', ['id'], unique=False)


def downgrade():
    # Drop tables
    op.drop_index(op.f('ix_message_actions_id'), table_name='message_actions')
    op.drop_table('message_actions')
    
    op.drop_index(op.f('ix_message_delivery_logs_id'), table_name='message_delivery_logs')
    op.drop_table('message_delivery_logs')
    
    op.drop_index(op.f('ix_messages_id'), table_name='messages')
    op.drop_table('messages')
    
    op.drop_index(op.f('ix_conversations_id'), table_name='conversations')
    op.drop_table('conversations')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS sendertype')
    op.execute('DROP TYPE IF EXISTS messagestatus')
    op.execute('DROP TYPE IF EXISTS messagepriority')
    op.execute('DROP TYPE IF EXISTS messagetype')
