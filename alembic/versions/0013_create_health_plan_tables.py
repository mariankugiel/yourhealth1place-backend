"""Create health plan tables

Revision ID: 0013
Revises: 0012
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0013'
down_revision = '0012'
branch_labels = None
depends_on = None


def upgrade():
    # Check if tables already exist
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Create health_plan_goals table only if it doesn't exist
    if 'health_plan_goals' not in inspector.get_table_names():
        op.create_table('health_plan_goals',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('connected_metric_id', sa.Integer(), nullable=True),
            sa.Column('target_operator', sa.String(length=20), nullable=True, default='equal'),
            sa.Column('target_value', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('baseline_value', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('current_value', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('progress_percentage', sa.Integer(), nullable=True, default=0),
            sa.Column('start_date', sa.Date(), nullable=False),
            sa.Column('end_date', sa.Date(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=False),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
            sa.ForeignKeyConstraint(['connected_metric_id'], ['health_record_metrics.id'], ),
            sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_health_plan_goals_id'), 'health_plan_goals', ['id'], unique=False)
    else:
        # Table exists, check if we need to add new columns
        existing_columns = [col['name'] for col in inspector.get_columns('health_plan_goals')]
        
        # Add new columns if they don't exist
        if 'target_value' not in existing_columns:
            op.add_column('health_plan_goals', sa.Column('target_value', sa.Numeric(precision=10, scale=2), nullable=True))
        if 'baseline_value' not in existing_columns:
            op.add_column('health_plan_goals', sa.Column('baseline_value', sa.Numeric(precision=10, scale=2), nullable=True))
        if 'current_value' not in existing_columns:
            op.add_column('health_plan_goals', sa.Column('current_value', sa.Numeric(precision=10, scale=2), nullable=True))
        if 'progress_percentage' not in existing_columns:
            op.add_column('health_plan_goals', sa.Column('progress_percentage', sa.Integer(), nullable=True, default=0))
        
        # Update target_operator column type if it's JSON
        try:
            # Check if target_operator is JSON type and needs to be converted to String
            target_operator_col = next(col for col in inspector.get_columns('health_plan_goals') if col['name'] == 'target_operator')
            if hasattr(target_operator_col['type'], '__class__') and 'JSON' in str(target_operator_col['type'].__class__):
                # Drop and recreate the column as String
                op.drop_column('health_plan_goals', 'target_operator')
                op.add_column('health_plan_goals', sa.Column('target_operator', sa.String(length=20), nullable=True, default='equal'))
        except:
            # Column doesn't exist or is already the correct type
            pass
    
    # Create health_plan_tasks table only if it doesn't exist
    if 'health_plan_tasks' not in inspector.get_table_names():
        op.create_table('health_plan_tasks',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('frequency', sa.String(length=20), nullable=False),
            sa.Column('target_days', sa.Integer(), nullable=True),
            sa.Column('time_of_day', sa.String(length=20), nullable=True),
            sa.Column('goal_id', sa.Integer(), nullable=True),
            sa.Column('metric_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=False),
            sa.Column('updated_by', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
            sa.ForeignKeyConstraint(['goal_id'], ['health_plan_goals.id'], ),
            sa.ForeignKeyConstraint(['metric_id'], ['health_record_metrics.id'], ),
            sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_health_plan_tasks_id'), 'health_plan_tasks', ['id'], unique=False)
    
    # Create health_plan_task_completions table only if it doesn't exist
    if 'health_plan_task_completions' not in inspector.get_table_names():
        op.create_table('health_plan_task_completions',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('task_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('completion_date', sa.Date(), nullable=False),
            sa.Column('completed', sa.Boolean(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['task_id'], ['health_plan_tasks.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_health_plan_task_completions_id'), 'health_plan_task_completions', ['id'], unique=False)
        
        # Create unique constraint for task/user/date combination
        op.create_unique_constraint('uq_health_plan_task_completions_task_user_date', 'health_plan_task_completions', 
                                   ['task_id', 'user_id', 'completion_date'])
        
        # Create indexes for better query performance
        op.create_index('ix_health_plan_task_completions_user_date', 'health_plan_task_completions', ['user_id', 'completion_date'])
        op.create_index('ix_health_plan_task_completions_task_date', 'health_plan_task_completions', ['task_id', 'completion_date'])


def downgrade():
    # Check if tables exist before dropping
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    if 'health_plan_task_completions' in inspector.get_table_names():
        try:
            op.drop_index('ix_health_plan_task_completions_task_date', table_name='health_plan_task_completions')
        except:
            pass
        try:
            op.drop_index('ix_health_plan_task_completions_user_date', table_name='health_plan_task_completions')
        except:
            pass
        try:
            op.drop_constraint('uq_health_plan_task_completions_task_user_date', 'health_plan_task_completions', type_='unique')
        except:
            pass
        try:
            op.drop_index(op.f('ix_health_plan_task_completions_id'), table_name='health_plan_task_completions')
        except:
            pass
        op.drop_table('health_plan_task_completions')
    
    if 'health_plan_tasks' in inspector.get_table_names():
        try:
            op.drop_index(op.f('ix_health_plan_tasks_id'), table_name='health_plan_tasks')
        except:
            pass
        op.drop_table('health_plan_tasks')
    
    if 'health_plan_goals' in inspector.get_table_names():
        try:
            op.drop_index(op.f('ix_health_plan_goals_id'), table_name='health_plan_goals')
        except:
            pass
        op.drop_table('health_plan_goals')