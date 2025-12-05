"""Add version to entry tables and content_version to translations table

Revision ID: 0026
Revises: 0025
Create Date: 2025-01-27 19:00:00.000000

This migration adds:
1. version column to medical_conditions, family_medical_history, surgeries_hospitalizations tables
2. content_version column to translations table

Version tracking ensures translations are re-created when source content changes.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0026'
down_revision = '0025'
branch_labels = None
depends_on = None


def upgrade():
    """Add version columns to entry tables and content_version to translations table"""
    
    # Check if tables exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # Add version to medical_conditions table
    if 'medical_conditions' in tables:
        op.add_column(
            'medical_conditions',
            sa.Column('version', sa.Integer(), nullable=False, server_default='1')
        )
    
    # Add version to family_medical_history table
    if 'family_medical_history' in tables:
        op.add_column(
            'family_medical_history',
            sa.Column('version', sa.Integer(), nullable=False, server_default='1')
        )
    
    # Add version to surgeries_hospitalizations table
    if 'surgeries_hospitalizations' in tables:
        op.add_column(
            'surgeries_hospitalizations',
            sa.Column('version', sa.Integer(), nullable=False, server_default='1')
        )
    
    # Add content_version to translations table
    if 'translations' in tables:
        op.add_column(
            'translations',
            sa.Column('content_version', sa.Integer(), nullable=True)
        )


def downgrade():
    """Remove version columns from entry tables and content_version from translations table"""
    
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # Remove content_version from translations table
    if 'translations' in tables:
        try:
            op.drop_column('translations', 'content_version')
        except Exception:
            pass
    
    # Remove version from surgeries_hospitalizations table
    if 'surgeries_hospitalizations' in tables:
        try:
            op.drop_column('surgeries_hospitalizations', 'version')
        except Exception:
            pass
    
    # Remove version from family_medical_history table
    if 'family_medical_history' in tables:
        try:
            op.drop_column('family_medical_history', 'version')
        except Exception:
            pass
    
    # Remove version from medical_conditions table
    if 'medical_conditions' in tables:
        try:
            op.drop_column('medical_conditions', 'version')
        except Exception:
            pass

