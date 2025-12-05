"""Add source_language to medical_conditions, family_medical_history, and surgeries_hospitalizations tables

Revision ID: 0025
Revises: 0024
Create Date: 2025-01-27 18:00:00.000000

This migration adds source_language column to:
- medical_conditions table
- family_medical_history table
- surgeries_hospitalizations table
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0025'
down_revision = '0024'
branch_labels = None
depends_on = None


def upgrade():
    """Add source_language columns to medical_conditions, family_medical_history, and surgeries_hospitalizations tables"""
    
    # Check if tables exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # Add source_language to medical_conditions table
    if 'medical_conditions' in tables:
        op.add_column(
            'medical_conditions',
            sa.Column('source_language', sa.String(10), nullable=False, server_default='en')
        )
    
    # Add source_language to family_medical_history table
    if 'family_medical_history' in tables:
        op.add_column(
            'family_medical_history',
            sa.Column('source_language', sa.String(10), nullable=False, server_default='en')
        )
    
    # Add source_language to surgeries_hospitalizations table
    if 'surgeries_hospitalizations' in tables:
        op.add_column(
            'surgeries_hospitalizations',
            sa.Column('source_language', sa.String(10), nullable=False, server_default='en')
        )


def downgrade():
    """Remove source_language columns from medical_conditions, family_medical_history, and surgeries_hospitalizations tables"""
    
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    # Remove source_language from surgeries_hospitalizations table
    if 'surgeries_hospitalizations' in tables:
        try:
            op.drop_column('surgeries_hospitalizations', 'source_language')
        except Exception:
            pass
    
    # Remove source_language from family_medical_history table
    if 'family_medical_history' in tables:
        try:
            op.drop_column('family_medical_history', 'source_language')
        except Exception:
            pass
    
    # Remove source_language from medical_conditions table
    if 'medical_conditions' in tables:
        try:
            op.drop_column('medical_conditions', 'source_language')
        except Exception:
            pass

