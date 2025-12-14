"""Remove recorded_at and rename timestamps to datetime with timezone

Revision ID: 0004
Revises: 0003
Create Date: 2024-12-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old indexes
    op.drop_index('ix_health_records_start_timestamp', table_name='health_records')
    
    # Rename columns and change type to datetime with timezone
    op.alter_column('health_records', 'start_timestamp',
                    new_column_name='measure_start_time',
                    type_=sa.DateTime(timezone=True),
                    existing_type=sa.DateTime(),
                    existing_nullable=True)
    
    op.alter_column('health_records', 'end_timestamp',
                    new_column_name='measure_end_time',
                    type_=sa.DateTime(timezone=True),
                    existing_type=sa.DateTime(),
                    existing_nullable=True)
    
    # Drop recorded_at column
    op.drop_column('health_records', 'recorded_at')
    
    # Create new indexes with new column names
    op.create_index('ix_health_records_measure_start_time', 'health_records', ['measure_start_time'], unique=False)


def downgrade() -> None:
    # Drop new indexes
    op.drop_index('ix_health_records_measure_start_time', table_name='health_records')
    
    # Add back recorded_at column
    op.add_column('health_records', sa.Column('recorded_at', sa.DateTime(), nullable=False, server_default=sa.func.now()))
    
    # Rename columns back and change type to datetime without timezone
    op.alter_column('health_records', 'measure_start_time',
                    new_column_name='start_timestamp',
                    type_=sa.DateTime(),
                    existing_type=sa.DateTime(timezone=True),
                    existing_nullable=True)
    
    op.alter_column('health_records', 'measure_end_time',
                    new_column_name='end_timestamp',
                    type_=sa.DateTime(),
                    existing_type=sa.DateTime(timezone=True),
                    existing_nullable=True)
    
    # Recreate old index
    op.create_index('ix_health_records_start_timestamp', 'health_records', ['start_timestamp'], unique=False)

