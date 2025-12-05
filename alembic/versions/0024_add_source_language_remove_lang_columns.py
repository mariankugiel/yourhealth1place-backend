"""Add source_language and remove language-specific columns from template tables

Revision ID: 0024
Revises: 0023
Create Date: 2025-01-27 16:00:00.000000

This migration:
1. Adds source_language column to template and user tables
2. Removes language-specific columns (name_pt, display_name_pt, etc.) from template tables
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0024'
down_revision = '0023'
branch_labels = None
depends_on = None


def upgrade():
    """Add source_language columns and remove language-specific columns"""
    
    # Check if tables exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # Add source_language to template tables
    if 'health_record_sections_tmp' in tables:
        # Add source_language column
        op.add_column(
            'health_record_sections_tmp',
            sa.Column('source_language', sa.String(10), nullable=True, server_default='en')
        )
        
        # Remove language-specific columns
        try:
            op.drop_column('health_record_sections_tmp', 'name_pt')
        except Exception:
            pass  # Column may not exist
        try:
            op.drop_column('health_record_sections_tmp', 'display_name_pt')
        except Exception:
            pass
        try:
            op.drop_column('health_record_sections_tmp', 'name_es')
        except Exception:
            pass
        try:
            op.drop_column('health_record_sections_tmp', 'display_name_es')
        except Exception:
            pass
    
    if 'health_record_metrics_tmp' in tables:
        # Add source_language column
        op.add_column(
            'health_record_metrics_tmp',
            sa.Column('source_language', sa.String(10), nullable=True, server_default='en')
        )
        
        # Remove language-specific columns
        try:
            op.drop_column('health_record_metrics_tmp', 'name_pt')
        except Exception:
            pass
        try:
            op.drop_column('health_record_metrics_tmp', 'display_name_pt')
        except Exception:
            pass
        try:
            op.drop_column('health_record_metrics_tmp', 'name_es')
        except Exception:
            pass
        try:
            op.drop_column('health_record_metrics_tmp', 'display_name_es')
        except Exception:
            pass
        try:
            op.drop_column('health_record_metrics_tmp', 'default_unit_pt')
        except Exception:
            pass
        try:
            op.drop_column('health_record_metrics_tmp', 'default_unit_es')
        except Exception:
            pass
    
    # Add source_language to user tables (for future use)
    if 'health_record_sections' in tables:
        op.add_column(
            'health_record_sections',
            sa.Column('source_language', sa.String(10), nullable=True, server_default='en')
        )
    
    if 'health_record_metrics' in tables:
        op.add_column(
            'health_record_metrics',
            sa.Column('source_language', sa.String(10), nullable=True, server_default='en')
        )


def downgrade():
    """Revert changes: remove source_language and restore language columns"""
    
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # Remove source_language from user tables
    if 'health_record_metrics' in tables:
        try:
            op.drop_column('health_record_metrics', 'source_language')
        except Exception:
            pass
    
    if 'health_record_sections' in tables:
        try:
            op.drop_column('health_record_sections', 'source_language')
        except Exception:
            pass
    
    # Restore language columns and remove source_language from template tables
    if 'health_record_metrics_tmp' in tables:
        try:
            op.drop_column('health_record_metrics_tmp', 'source_language')
        except Exception:
            pass
        
        # Restore columns (nullable since we don't have the old data)
        try:
            op.add_column('health_record_metrics_tmp', sa.Column('default_unit_es', sa.Text(), nullable=True))
        except Exception:
            pass
        try:
            op.add_column('health_record_metrics_tmp', sa.Column('default_unit_pt', sa.Text(), nullable=True))
        except Exception:
            pass
        try:
            op.add_column('health_record_metrics_tmp', sa.Column('display_name_es', sa.Text(), nullable=True))
        except Exception:
            pass
        try:
            op.add_column('health_record_metrics_tmp', sa.Column('name_es', sa.Text(), nullable=True))
        except Exception:
            pass
        try:
            op.add_column('health_record_metrics_tmp', sa.Column('display_name_pt', sa.Text(), nullable=True))
        except Exception:
            pass
        try:
            op.add_column('health_record_metrics_tmp', sa.Column('name_pt', sa.Text(), nullable=True))
        except Exception:
            pass
    
    if 'health_record_sections_tmp' in tables:
        try:
            op.drop_column('health_record_sections_tmp', 'source_language')
        except Exception:
            pass
        
        # Restore columns
        try:
            op.add_column('health_record_sections_tmp', sa.Column('display_name_es', sa.Text(), nullable=True))
        except Exception:
            pass
        try:
            op.add_column('health_record_sections_tmp', sa.Column('name_es', sa.Text(), nullable=True))
        except Exception:
            pass
        try:
            op.add_column('health_record_sections_tmp', sa.Column('display_name_pt', sa.Text(), nullable=True))
        except Exception:
            pass
        try:
            op.add_column('health_record_sections_tmp', sa.Column('name_pt', sa.Text(), nullable=True))
        except Exception:
            pass

