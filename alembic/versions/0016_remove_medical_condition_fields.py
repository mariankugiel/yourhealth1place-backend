"""Remove unused fields from medical_conditions table

Revision ID: 0016_remove_medical_condition_fields
Revises: 0013_create_health_plan_tables
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0016'
down_revision = '0013'
branch_labels = None
depends_on = None


def upgrade():
    """Remove severity, current_medications, and outcome columns from medical_conditions table"""
    
    # Check if the medical_conditions table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'medical_conditions' in inspector.get_table_names():
        # Check if columns exist before dropping them
        columns = [col['name'] for col in inspector.get_columns('medical_conditions')]
        
        # Drop severity column if it exists
        if 'severity' in columns:
            print("Dropping 'severity' column from medical_conditions table...")
            op.drop_column('medical_conditions', 'severity')
        
        # Drop current_medications column if it exists
        if 'current_medications' in columns:
            print("Dropping 'current_medications' column from medical_conditions table...")
            op.drop_column('medical_conditions', 'current_medications')
        
        # Drop outcome column if it exists
        if 'outcome' in columns:
            print("Dropping 'outcome' column from medical_conditions table...")
            op.drop_column('medical_conditions', 'outcome')
        
        print("Successfully removed unused fields from medical_conditions table")
    else:
        print("medical_conditions table does not exist, skipping migration")


def downgrade():
    """Add back the removed columns (for rollback purposes)"""
    
    # Check if the medical_conditions table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'medical_conditions' in inspector.get_table_names():
        # Check if columns exist before adding them back
        columns = [col['name'] for col in inspector.get_columns('medical_conditions')]
        
        # Add back severity column if it doesn't exist
        if 'severity' not in columns:
            print("Adding back 'severity' column to medical_conditions table...")
            op.add_column('medical_conditions', 
                         sa.Column('severity', postgresql.ENUM('mild', 'moderate', 'severe', name='conditionseverity'), nullable=True))
        
        # Add back current_medications column if it doesn't exist
        if 'current_medications' not in columns:
            print("Adding back 'current_medications' column to medical_conditions table...")
            op.add_column('medical_conditions', 
                         sa.Column('current_medications', postgresql.JSON(astext_type=sa.Text()), nullable=True))
        
        # Add back outcome column if it doesn't exist
        if 'outcome' not in columns:
            print("Adding back 'outcome' column to medical_conditions table...")
            op.add_column('medical_conditions', 
                         sa.Column('outcome', sa.Text(), nullable=True))
        
        print("Successfully added back removed fields to medical_conditions table")
    else:
        print("medical_conditions table does not exist, skipping rollback")
