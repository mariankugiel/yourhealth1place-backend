"""enhance family medical history schema

Revision ID: 0004
Revises: None
Create Date: 2025-10-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0004'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Check if columns already exist before adding them
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Get existing columns
    existing_columns = [col['name'] for col in inspector.get_columns('family_medical_history')]
    
    # Add new columns only if they don't exist
    if 'is_deceased' not in existing_columns:
        op.add_column('family_medical_history', sa.Column('is_deceased', sa.Boolean(), nullable=False, server_default='false'))
    
    if 'age_at_death' not in existing_columns:
        op.add_column('family_medical_history', sa.Column('age_at_death', sa.Integer(), nullable=True))
    
    if 'cause_of_death' not in existing_columns:
        op.add_column('family_medical_history', sa.Column('cause_of_death', sa.String(500), nullable=True))
    
    if 'current_age' not in existing_columns:
        op.add_column('family_medical_history', sa.Column('current_age', sa.Integer(), nullable=True))
    
    if 'gender' not in existing_columns:
        op.add_column('family_medical_history', sa.Column('gender', sa.String(20), nullable=True))
    
    if 'chronic_diseases' not in existing_columns:
        op.add_column('family_medical_history', sa.Column('chronic_diseases', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    # Make legacy columns nullable for backward compatibility (check if column exists)
    if 'condition_name' in existing_columns:
        # Check if it's already nullable
        columns_info = inspector.get_columns('family_medical_history')
        condition_name_col = next((col for col in columns_info if col['name'] == 'condition_name'), None)
        if condition_name_col and not condition_name_col.get('nullable', False):
            op.alter_column('family_medical_history', 'condition_name', nullable=True)


def downgrade():
    # Remove new columns
    op.drop_column('family_medical_history', 'chronic_diseases')
    op.drop_column('family_medical_history', 'gender')
    op.drop_column('family_medical_history', 'current_age')
    op.drop_column('family_medical_history', 'cause_of_death')
    op.drop_column('family_medical_history', 'age_at_death')
    op.drop_column('family_medical_history', 'is_deceased')
    
    # Restore condition_name as required
    op.alter_column('family_medical_history', 'condition_name', nullable=False)

