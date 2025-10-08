"""Add medication reminder system tables

Revision ID: 0001
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add timezone column to users table
    op.add_column('users', sa.Column('timezone', sa.String(50), nullable=True, default='UTC'))
    
    # Create medication_reminders table
    op.create_table('medication_reminders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('medication_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('reminder_time', sa.Time(), nullable=False),
        sa.Column('user_timezone', sa.String(50), nullable=False, default='UTC'),
        sa.Column('days_of_week', sa.JSON(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('next_scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.Enum('active', 'paused', 'deleted', name='reminderstatus'), nullable=True, default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['medication_id'], ['medications.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_reminders_id'), 'medication_reminders', ['id'], unique=False)
    
    # Create notifications table
    op.create_table('notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.Enum('medication_reminder', 'appointment_reminder', 'health_alert', 'system_message', name='notificationtype'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('medication_id', sa.Integer(), nullable=True),
        sa.Column('appointment_id', sa.Integer(), nullable=True),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum('unread', 'read', 'dismissed', name='notificationstatus'), nullable=True, default='unread'),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('display_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ),
        sa.ForeignKeyConstraint(['medication_id'], ['medications.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    
    # Create websocket_connections table
    op.create_table('websocket_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.String(255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('connected_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_ping_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_websocket_connections_id'), 'websocket_connections', ['id'], unique=False)
    op.create_index(op.f('ix_websocket_connections_connection_id'), 'websocket_connections', ['connection_id'], unique=True)


def downgrade():
    # Drop websocket_connections table
    op.drop_index(op.f('ix_websocket_connections_connection_id'), table_name='websocket_connections')
    op.drop_index(op.f('ix_websocket_connections_id'), table_name='websocket_connections')
    op.drop_table('websocket_connections')
    
    # Drop notifications table
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')
    
    # Drop medication_reminders table
    op.drop_index(op.f('ix_medication_reminders_id'), table_name='medication_reminders')
    op.drop_table('medication_reminders')
    
    # Remove timezone column from users table
    op.drop_column('users', 'timezone')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS reminderstatus')
    op.execute('DROP TYPE IF EXISTS notificationtype')
    op.execute('DROP TYPE IF EXISTS notificationstatus')
