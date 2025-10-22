"""Add progress_count to task completion

Revision ID: 0018
Revises: 0017
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0018'
down_revision = '0017'
branch_labels = None
depends_on = None


def upgrade():
    # Add progress_count column to health_plan_task_completions table
    op.add_column('health_plan_task_completions', 
                  sa.Column('progress_count', sa.Integer(), nullable=True, default=0))
    
    # Update existing records to have progress_count = 1 where completed = True
    op.execute("""
        UPDATE health_plan_task_completions 
        SET progress_count = 1 
        WHERE completed = true
    """)
    
    # Update existing records to have progress_count = 0 where completed = False
    op.execute("""
        UPDATE health_plan_task_completions 
        SET progress_count = 0 
        WHERE completed = false
    """)


def downgrade():
    # Remove progress_count column
    op.drop_column('health_plan_task_completions', 'progress_count')
