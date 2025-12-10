"""Add translation support to health plans and medications

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add translation support to health_plan_goals table
    op.add_column('health_plan_goals', sa.Column('source_language', sa.String(length=10), nullable=False, server_default='en'))
    op.add_column('health_plan_goals', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    
    # Add translation support to health_plan_tasks table
    op.add_column('health_plan_tasks', sa.Column('source_language', sa.String(length=10), nullable=False, server_default='en'))
    op.add_column('health_plan_tasks', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    
    # Add translation support to medications table
    op.add_column('medications', sa.Column('source_language', sa.String(length=10), nullable=False, server_default='en'))
    op.add_column('medications', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))


def downgrade() -> None:
    # Remove translation support from medications table
    op.drop_column('medications', 'version')
    op.drop_column('medications', 'source_language')
    
    # Remove translation support from health_plan_tasks table
    op.drop_column('health_plan_tasks', 'version')
    op.drop_column('health_plan_tasks', 'source_language')
    
    # Remove translation support from health_plan_goals table
    op.drop_column('health_plan_goals', 'version')
    op.drop_column('health_plan_goals', 'source_language')

