"""Update health goals schema and remove unused tracking tables

Revision ID: 0011
Revises: 0010
Create Date: 2025-01-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0011'
down_revision = '0010'
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    
    # Step 1: Drop unused tracking tables first (to avoid foreign key constraints)
    try:
        op.drop_table('goal_tracking_details')
    except:
        pass  # Table might not exist
    
    try:
        op.drop_table('goal_tracking')
    except:
        pass  # Table might not exist
    
    # Step 2: Check current state and handle table renaming properly
    # Check if goals table exists
    try:
        goals_exists = connection.execute(sa.text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'goals'
            )
        """)).scalar()
    except:
        goals_exists = False
    
    # Check if health_goals table exists
    try:
        health_goals_exists = connection.execute(sa.text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'health_goals'
            )
        """)).scalar()
    except:
        health_goals_exists = False
    
    # Handle table rename only if needed
    if goals_exists and not health_goals_exists:
        # Need to update foreign key constraints before renaming
        try:
            op.drop_constraint('tasks_goal_id_fkey', 'tasks', type_='foreignkey')
        except:
            try:
                op.drop_constraint('fk_tasks_goal_id', 'tasks', type_='foreignkey')
            except:
                pass
        
        op.rename_table('goals', 'health_goals')
        
        # Recreate foreign key constraint
        try:
            op.create_foreign_key('tasks_goal_id_fkey', 'tasks', 'health_goals', ['goal_id'], ['id'])
        except:
            pass
    elif not goals_exists and health_goals_exists:
        # health_goals already exists, just ensure foreign key is correct
        try:
            op.create_foreign_key('tasks_goal_id_fkey', 'tasks', 'health_goals', ['goal_id'], ['id'])
        except:
            pass
    
    # Step 3: Add start_date column to health_goals table if it doesn't exist
    try:
        # Check if column exists first
        column_exists = connection.execute(sa.text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'health_goals'
                AND column_name = 'start_date'
            )
        """)).scalar()
        
        if not column_exists:
            op.add_column('health_goals', sa.Column('start_date', sa.Date(), nullable=True))
    except:
        # If there's an error checking, just try to add the column
        try:
            op.add_column('health_goals', sa.Column('start_date', sa.Date(), nullable=True))
        except:
            pass
    
    # Step 4: Remove unused columns from health_goals table
    columns_to_remove = [
        'progress_percentage', 'owner_type', 'owner_id', 'health_plan_id', 
        'status', 'priority', 'auto_track', 'goal_type', 'description'
    ]
    
    for column_name in columns_to_remove:
        try:
            # Check if column exists first
            column_exists = connection.execute(sa.text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'health_goals'
                    AND column_name = :column_name
                )
            """), {'column_name': column_name}).scalar()
            
            if column_exists:
                op.drop_column('health_goals', column_name)
        except:
            # If there's an error checking or dropping, just try to drop
            try:
                op.drop_column('health_goals', column_name)
            except:
                pass  # Column might not exist or already removed


def downgrade():
    # Reverse the process
    
    # Step 1: Re-add the columns we removed (with appropriate defaults)
    op.add_column('health_goals', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('health_goals', sa.Column('goal_type', sa.String(50), nullable=True))
    op.add_column('health_goals', sa.Column('auto_track', sa.Boolean(), nullable=True, default=False))
    op.add_column('health_goals', sa.Column('priority', sa.String(20), nullable=True))
    op.add_column('health_goals', sa.Column('status', sa.String(50), nullable=True))
    op.add_column('health_goals', sa.Column('health_plan_id', sa.Integer(), nullable=True))
    op.add_column('health_goals', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.add_column('health_goals', sa.Column('owner_type', sa.String(20), nullable=True))
    op.add_column('health_goals', sa.Column('progress_percentage', sa.Integer(), nullable=True, default=0))
    
    # Step 2: Remove start_date column
    op.drop_column('health_goals', 'start_date')
    
    # Step 3: Update Task table foreign key reference before renaming back
    try:
        op.drop_constraint('tasks_goal_id_fkey', 'tasks', type_='foreignkey')
    except:
        try:
            op.drop_constraint('fk_tasks_goal_id', 'tasks', type_='foreignkey')
        except:
            try:
                op.drop_constraint('tasks_ibfk_goal_id', 'tasks', type_='foreignkey')
            except:
                pass
    
    # Step 4: Rename health_goals table back to goals
    op.rename_table('health_goals', 'goals')
    
    # Step 5: Recreate the foreign key constraint with original table name
    op.create_foreign_key('tasks_goal_id_fkey', 'tasks', 'goals', ['goal_id'], ['id'])
    
    # Step 6: Recreate the tracking tables (Note: this will lose any existing data)
    
    # Create goal_tracking table
    op.create_table('goal_tracking',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('goal_id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('tracking_date', sa.Date(), nullable=False),
        sa.Column('target_count', sa.Integer(), nullable=False),
        sa.Column('completed_count', sa.Integer(), nullable=True, default=0),
        sa.Column('status', sa.String(50), nullable=False, default='PENDING'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ),
        sa.ForeignKeyConstraint(['patient_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goal_tracking_id'), 'goal_tracking', ['id'], unique=False)
    
    # Create goal_tracking_details table
    op.create_table('goal_tracking_details',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('goal_tracking_id', sa.Integer(), nullable=False),
        sa.Column('goal_id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('measurement_time', sa.DateTime(), nullable=False),
        sa.Column('measurement_value', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('health_record_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ),
        sa.ForeignKeyConstraint(['goal_tracking_id'], ['goal_tracking.id'], ),
        sa.ForeignKeyConstraint(['health_record_id'], ['health_records.id'], ),
        sa.ForeignKeyConstraint(['patient_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goal_tracking_details_id'), 'goal_tracking_details', ['id'], unique=False)
