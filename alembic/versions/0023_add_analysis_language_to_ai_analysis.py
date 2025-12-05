"""Add analysis_language to ai_analysis_history

Revision ID: 0023
Revises: 0022
Create Date: 2025-01-27 15:00:00.000000

This migration adds the analysis_language field to track which language
the AI analysis was generated in.

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0023'
down_revision = '0022'
branch_labels = None
depends_on = None


def upgrade():
    """Add analysis_language column to ai_analysis_history table"""
    
    # Check if table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'ai_analysis_history' not in inspector.get_table_names():
        print("ai_analysis_history table does not exist, skipping migration")
        return
    
    # Add analysis_language column
    op.add_column(
        'ai_analysis_history',
        sa.Column('analysis_language', sa.String(10), nullable=True, server_default='en')
    )


def downgrade():
    """Remove analysis_language column from ai_analysis_history table"""
    
    # Drop column
    op.drop_column('ai_analysis_history', 'analysis_language')


