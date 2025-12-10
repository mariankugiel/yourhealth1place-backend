"""Add Thryve tables

Revision ID: 0002
Revises: 0001
Create Date: 2024-12-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create thryve_data_types table
    op.create_table(
        'thryve_data_types',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('data_type_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=255), nullable=True),
        sa.Column('type', sa.Enum('Daily', 'Epoch', name='thryvedailyepoch'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('unit', sa.String(length=100), nullable=True),
        sa.Column('value_type', sa.String(length=50), nullable=True),
        sa.Column('platform_support', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('data_type_id')
    )
    op.create_index('ix_thryve_data_types_data_type_id', 'thryve_data_types', ['data_type_id'], unique=True)
    op.create_index('ix_thryve_data_types_name', 'thryve_data_types', ['name'], unique=False)
    op.create_index('ix_thryve_data_types_type', 'thryve_data_types', ['type'], unique=False)
    
    # Create thryve_data_sources table
    op.create_table(
        'thryve_data_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('data_source_type', sa.String(length=50), nullable=True),
        sa.Column('retrieval_method', sa.String(length=50), nullable=True),
        sa.Column('historic_data', sa.Boolean(), nullable=True),
        sa.Column('shared_oauth_client', sa.String(length=10), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_thryve_data_sources_id', 'thryve_data_sources', ['id'], unique=True)
    op.create_index('ix_thryve_data_sources_name', 'thryve_data_sources', ['name'], unique=False)
    
    # Add thryve_data_type_id to health_record_metrics_tmp
    op.add_column('health_record_metrics_tmp', sa.Column('thryve_data_type_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_health_record_metrics_tmp_thryve_data_type',
        'health_record_metrics_tmp',
        'thryve_data_types',
        ['thryve_data_type_id'],
        ['id']
    )
    op.create_index('ix_health_record_metrics_tmp_thryve_data_type_id', 'health_record_metrics_tmp', ['thryve_data_type_id'], unique=False)


def downgrade() -> None:
    # Remove thryve_data_type_id from health_record_metrics_tmp
    op.drop_index('ix_health_record_metrics_tmp_thryve_data_type_id', table_name='health_record_metrics_tmp')
    op.drop_constraint('fk_health_record_metrics_tmp_thryve_data_type', 'health_record_metrics_tmp', type_='foreignkey')
    op.drop_column('health_record_metrics_tmp', 'thryve_data_type_id')
    
    # Drop thryve_data_sources table
    op.drop_index('ix_thryve_data_sources_name', table_name='thryve_data_sources')
    op.drop_index('ix_thryve_data_sources_id', table_name='thryve_data_sources')
    op.drop_table('thryve_data_sources')
    
    # Drop thryve_data_types table
    op.drop_index('ix_thryve_data_types_type', table_name='thryve_data_types')
    op.drop_index('ix_thryve_data_types_name', table_name='thryve_data_types')
    op.drop_index('ix_thryve_data_types_data_type_id', table_name='thryve_data_types')
    op.drop_table('thryve_data_types')
    
    # Drop enum type
    op.execute("DROP TYPE IF EXISTS thryvedailyepoch")

