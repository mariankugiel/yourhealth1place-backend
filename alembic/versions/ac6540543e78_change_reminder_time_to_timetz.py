"""change reminder_time to timetz

Revision ID: ac6540543e78
Revises: remove_email_unique_constraint
Create Date: 2025-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ac6540543e78'
down_revision = 'remove_email_unique_constraint'
branch_labels = None
depends_on = None


def upgrade():
    """Change reminder_time from TIME to TIMETZ (time with timezone)"""
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Check if medication_reminders table exists
    if 'medication_reminders' not in inspector.get_table_names():
        print("medication_reminders table does not exist, skipping migration")
        return
    
    # Get column info
    columns = inspector.get_columns('medication_reminders')
    reminder_time_col = next((col for col in columns if col['name'] == 'reminder_time'), None)
    
    if not reminder_time_col:
        print("reminder_time column does not exist, skipping migration")
        return
    
    # Check current type
    current_type = str(reminder_time_col['type'])
    if 'timetz' in current_type.lower() or 'time with time zone' in current_type.lower():
        print("reminder_time is already TIMETZ, skipping migration")
        return
    
    # Convert TIME to TIMETZ
    # We need to convert existing TIME values to TIMETZ using the user_timezone
    # For existing data, we'll set timezone to UTC as default, then the application
    # will use user_timezone column for proper timezone handling
    op.execute("""
        ALTER TABLE medication_reminders 
        ALTER COLUMN reminder_time TYPE TIME WITH TIME ZONE 
        USING reminder_time AT TIME ZONE 'UTC'
    """)
    
    print("✅ Changed reminder_time from TIME to TIMETZ")


def downgrade():
    """Revert reminder_time from TIMETZ back to TIME"""
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    if 'medication_reminders' not in inspector.get_table_names():
        return
    
    # Convert TIMETZ back to TIME (loses timezone info)
    op.execute("""
        ALTER TABLE medication_reminders 
        ALTER COLUMN reminder_time TYPE TIME 
        USING reminder_time::TIME
    """)
    
    print("✅ Reverted reminder_time from TIMETZ to TIME")
