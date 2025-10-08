"""create reminder notification system

Revision ID: 0002
Revises: 0001
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    # Create medication_reminders table
    op.create_table(
        'medication_reminders',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('medication_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('reminder_time', sa.Time(), nullable=False),
        sa.Column('user_timezone', sa.String(length=50), nullable=False),
        sa.Column('days_of_week', sa.JSON(), nullable=False),
        sa.Column('next_scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.Enum('active', 'paused', 'completed', 'deleted', name='reminderstatus'), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['medication_id'], ['medications.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_reminders_id'), 'medication_reminders', ['id'], unique=False)
    op.create_index(op.f('ix_medication_reminders_status'), 'medication_reminders', ['status'], unique=False)
    op.create_index(op.f('ix_medication_reminders_next_scheduled_at'), 'medication_reminders', ['next_scheduled_at'], unique=False)

    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.Enum('medication_reminder', 'appointment_reminder', 'health_alert', 'system_message', 'admin_instruction', name='notificationtype'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('priority', sa.Enum('low', 'normal', 'high', 'urgent', name='notificationpriority'), nullable=True),
        sa.Column('medication_id', sa.Integer(), nullable=True),
        sa.Column('appointment_id', sa.Integer(), nullable=True),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'sent', 'delivered', 'read', 'failed', 'dismissed', name='notificationstatus'), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['medication_id'], ['medications.id'], ),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
    op.create_index(op.f('ix_notifications_notification_type'), 'notifications', ['notification_type'], unique=False)
    op.create_index(op.f('ix_notifications_status'), 'notifications', ['status'], unique=False)
    op.create_index(op.f('ix_notifications_scheduled_at'), 'notifications', ['scheduled_at'], unique=False)

    # Create notification_channels table
    op.create_table(
        'notification_channels',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('email_enabled', sa.Boolean(), nullable=True),
        sa.Column('email_address', sa.String(length=255), nullable=True),
        sa.Column('sms_enabled', sa.Boolean(), nullable=True),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('websocket_enabled', sa.Boolean(), nullable=True),
        sa.Column('web_push_enabled', sa.Boolean(), nullable=True),
        sa.Column('preferences', sa.JSON(), nullable=True),
        sa.Column('quiet_hours', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_notification_channels_id'), 'notification_channels', ['id'], unique=False)
    op.create_index(op.f('ix_notification_channels_user_id'), 'notification_channels', ['user_id'], unique=True)

    # Create websocket_connections table
    op.create_table(
        'websocket_connections',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('connection_id', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('connected_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_ping_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('disconnected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ttl', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('connection_id')
    )
    op.create_index(op.f('ix_websocket_connections_id'), 'websocket_connections', ['id'], unique=False)
    op.create_index(op.f('ix_websocket_connections_connection_id'), 'websocket_connections', ['connection_id'], unique=True)
    op.create_index(op.f('ix_websocket_connections_user_id'), 'websocket_connections', ['user_id'], unique=False)
    op.create_index(op.f('ix_websocket_connections_is_active'), 'websocket_connections', ['is_active'], unique=False)

    # Create web_push_subscriptions table
    op.create_table(
        'web_push_subscriptions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('endpoint', sa.Text(), nullable=False),
        sa.Column('p256dh_key', sa.Text(), nullable=False),
        sa.Column('auth_key', sa.Text(), nullable=False),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('browser', sa.String(length=100), nullable=True),
        sa.Column('device_type', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('subscribed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('unsubscribed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_attempts', sa.Integer(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('last_error_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('endpoint')
    )
    op.create_index(op.f('ix_web_push_subscriptions_id'), 'web_push_subscriptions', ['id'], unique=False)
    op.create_index(op.f('ix_web_push_subscriptions_user_id'), 'web_push_subscriptions', ['user_id'], unique=False)
    op.create_index(op.f('ix_web_push_subscriptions_is_active'), 'web_push_subscriptions', ['is_active'], unique=False)

    # Create notification_delivery_logs table
    op.create_table(
        'notification_delivery_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('notification_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('channel', sa.Enum('email', 'sms', 'websocket', 'web_push', name='deliverychannel'), nullable=False),
        sa.Column('status', sa.Enum('queued', 'sent', 'delivered', 'failed', 'bounced', 'rejected', name='deliverystatus'), nullable=False),
        sa.Column('target_address', sa.String(length=255), nullable=True),
        sa.Column('sqs_message_id', sa.String(length=255), nullable=True),
        sa.Column('sqs_receipt_handle', sa.Text(), nullable=True),
        sa.Column('provider_message_id', sa.String(length=255), nullable=True),
        sa.Column('provider_response', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(length=100), nullable=True),
        sa.Column('attempt_number', sa.Integer(), nullable=True),
        sa.Column('max_attempts', sa.Integer(), nullable=True),
        sa.Column('queued_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['notification_id'], ['notifications.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_delivery_logs_id'), 'notification_delivery_logs', ['id'], unique=False)
    op.create_index(op.f('ix_notification_delivery_logs_notification_id'), 'notification_delivery_logs', ['notification_id'], unique=False)
    op.create_index(op.f('ix_notification_delivery_logs_user_id'), 'notification_delivery_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_notification_delivery_logs_channel'), 'notification_delivery_logs', ['channel'], unique=False)
    op.create_index(op.f('ix_notification_delivery_logs_status'), 'notification_delivery_logs', ['status'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_notification_delivery_logs_status'), table_name='notification_delivery_logs')
    op.drop_index(op.f('ix_notification_delivery_logs_channel'), table_name='notification_delivery_logs')
    op.drop_index(op.f('ix_notification_delivery_logs_user_id'), table_name='notification_delivery_logs')
    op.drop_index(op.f('ix_notification_delivery_logs_notification_id'), table_name='notification_delivery_logs')
    op.drop_index(op.f('ix_notification_delivery_logs_id'), table_name='notification_delivery_logs')
    op.drop_table('notification_delivery_logs')
    
    op.drop_index(op.f('ix_web_push_subscriptions_is_active'), table_name='web_push_subscriptions')
    op.drop_index(op.f('ix_web_push_subscriptions_user_id'), table_name='web_push_subscriptions')
    op.drop_index(op.f('ix_web_push_subscriptions_id'), table_name='web_push_subscriptions')
    op.drop_table('web_push_subscriptions')
    
    op.drop_index(op.f('ix_websocket_connections_is_active'), table_name='websocket_connections')
    op.drop_index(op.f('ix_websocket_connections_user_id'), table_name='websocket_connections')
    op.drop_index(op.f('ix_websocket_connections_connection_id'), table_name='websocket_connections')
    op.drop_index(op.f('ix_websocket_connections_id'), table_name='websocket_connections')
    op.drop_table('websocket_connections')
    
    op.drop_index(op.f('ix_notification_channels_user_id'), table_name='notification_channels')
    op.drop_index(op.f('ix_notification_channels_id'), table_name='notification_channels')
    op.drop_table('notification_channels')
    
    op.drop_index(op.f('ix_notifications_scheduled_at'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_status'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_notification_type'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')
    
    op.drop_index(op.f('ix_medication_reminders_next_scheduled_at'), table_name='medication_reminders')
    op.drop_index(op.f('ix_medication_reminders_status'), table_name='medication_reminders')
    op.drop_index(op.f('ix_medication_reminders_id'), table_name='medication_reminders')
    op.drop_table('medication_reminders')
    
    # Drop enums
    sa.Enum(name='deliverystatus').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='deliverychannel').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='notificationpriority').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='notificationstatus').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='notificationtype').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='reminderstatus').drop(op.get_bind(), checkfirst=False)

