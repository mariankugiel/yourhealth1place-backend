"""Add target fields to health task

Revision ID: 0019
Revises: 0018
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0019'
down_revision = '0018'
branch_labels = None
depends_on = None


def upgrade():
    # Add target fields to health_plan_tasks table
    op.add_column('health_plan_tasks', sa.Column('target_operator', sa.String(20), nullable=True))
    op.add_column('health_plan_tasks', sa.Column('target_value', sa.String(50), nullable=True))
    op.add_column('health_plan_tasks', sa.Column('target_unit', sa.String(20), nullable=True))


def downgrade():
    # Remove target fields from health_plan_tasks table
    op.drop_column('health_plan_tasks', 'target_unit')
    op.drop_column('health_plan_tasks', 'target_value')
    op.drop_column('health_plan_tasks', 'target_operator')
