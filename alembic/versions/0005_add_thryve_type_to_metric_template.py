"""Add thryve_type column to health_record_metrics_tmp

Revision ID: 0005
Revises: 0004
Create Date: 2024-12-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0005'
down_revision: Union[str, None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add thryve_type column to health_record_metrics_tmp table
    op.add_column('health_record_metrics_tmp', 
                  sa.Column('thryve_type', sa.String(20), nullable=True))


def downgrade() -> None:
    # Remove thryve_type column
    op.drop_column('health_record_metrics_tmp', 'thryve_type')

