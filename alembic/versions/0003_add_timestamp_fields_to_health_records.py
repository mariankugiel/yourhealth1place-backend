"""Add timestamp fields to health records

Revision ID: 0003
Revises: 0002
Create Date: 2024-12-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add start_timestamp column (nullable, for epoch data start time and daily data day start)
    op.add_column('health_records', sa.Column('start_timestamp', sa.DateTime(), nullable=True))
    
    # Add end_timestamp column (nullable, for epoch data end time, null for daily data)
    op.add_column('health_records', sa.Column('end_timestamp', sa.DateTime(), nullable=True))
    
    # Add data_type column (nullable, 'epoch' or 'daily' to distinguish data types)
    op.add_column('health_records', sa.Column('data_type', sa.String(length=20), nullable=True))
    
    # Create index on data_type for faster filtering
    op.create_index('ix_health_records_data_type', 'health_records', ['data_type'], unique=False)
    
    # Create index on start_timestamp for faster date range queries
    op.create_index('ix_health_records_start_timestamp', 'health_records', ['start_timestamp'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_health_records_start_timestamp', table_name='health_records')
    op.drop_index('ix_health_records_data_type', table_name='health_records')
    
    # Drop columns
    op.drop_column('health_records', 'data_type')
    op.drop_column('health_records', 'end_timestamp')
    op.drop_column('health_records', 'start_timestamp')

