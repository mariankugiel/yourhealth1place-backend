"""update medications schema - make aws_file_id nullable and change date types

Revision ID: 0005
Revises: None
Create Date: 2025-10-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade():
    # Check if columns already exist before adding/modifying them
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Get existing columns
    existing_columns = [col['name'] for col in inspector.get_columns('medications')]
    
    # Add new medication detail columns only if they don't exist
    if 'dosage' not in existing_columns:
        op.add_column('medications', sa.Column('dosage', sa.String(100), nullable=True))
    
    if 'frequency' not in existing_columns:
        op.add_column('medications', sa.Column('frequency', sa.String(100), nullable=True))
    
    if 'purpose' not in existing_columns:
        op.add_column('medications', sa.Column('purpose', sa.String(500), nullable=True))
    
    if 'instructions' not in existing_columns:
        op.add_column('medications', sa.Column('instructions', sa.Text(), nullable=True))
    
    # Add prescription information columns
    if 'rx_number' not in existing_columns:
        op.add_column('medications', sa.Column('rx_number', sa.String(100), nullable=True))
    
    if 'pharmacy' not in existing_columns:
        op.add_column('medications', sa.Column('pharmacy', sa.String(255), nullable=True))
    
    if 'original_quantity' not in existing_columns:
        op.add_column('medications', sa.Column('original_quantity', sa.Integer(), nullable=True))
    
    if 'refills_remaining' not in existing_columns:
        op.add_column('medications', sa.Column('refills_remaining', sa.Integer(), nullable=True))
    
    if 'last_filled_date' not in existing_columns:
        op.add_column('medications', sa.Column('last_filled_date', sa.Date(), nullable=True))
    
    # Check the current type of start_date and end_date before changing
    columns_info = inspector.get_columns('medications')
    
    # Change start_date from DateTime to Date (if it's currently DateTime)
    if 'start_date' in existing_columns:
        start_date_col = next((col for col in columns_info if col['name'] == 'start_date'), None)
        if start_date_col and str(start_date_col['type']) not in ('DATE', 'Date'):
            op.alter_column('medications', 'start_date',
                            type_=sa.Date(),
                            existing_type=sa.DateTime(),
                            nullable=False,
                            postgresql_using='start_date::date')
    
    # Change end_date from DateTime to Date (if it's currently DateTime)
    if 'end_date' in existing_columns:
        end_date_col = next((col for col in columns_info if col['name'] == 'end_date'), None)
        if end_date_col and str(end_date_col['type']) not in ('DATE', 'Date'):
            op.alter_column('medications', 'end_date',
                            type_=sa.Date(),
                            existing_type=sa.DateTime(),
                            nullable=True,
                            postgresql_using='end_date::date')
    
    # Drop aws_file_id column (not needed for medications) if it exists
    if 'aws_file_id' in existing_columns:
        op.drop_column('medications', 'aws_file_id')


def downgrade():
    # Add back aws_file_id column
    op.add_column('medications', sa.Column('aws_file_id', sa.String(255), nullable=True))
    
    # Revert start_date from Date to DateTime
    op.alter_column('medications', 'start_date',
                    type_=sa.DateTime(),
                    existing_type=sa.Date(),
                    nullable=False)
    
    # Revert end_date from Date to DateTime
    op.alter_column('medications', 'end_date',
                    type_=sa.DateTime(),
                    existing_type=sa.Date(),
                    nullable=True)
    
    # Remove prescription information columns
    op.drop_column('medications', 'last_filled_date')
    op.drop_column('medications', 'refills_remaining')
    op.drop_column('medications', 'original_quantity')
    op.drop_column('medications', 'pharmacy')
    op.drop_column('medications', 'rx_number')
    
    # Remove new medication detail columns
    op.drop_column('medications', 'instructions')
    op.drop_column('medications', 'purpose')
    op.drop_column('medications', 'frequency')
    op.drop_column('medications', 'dosage')

