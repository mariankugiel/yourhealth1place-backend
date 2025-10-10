"""enhance family medical history schema

Revision ID: 0004
Revises: 0003
Create Date: 2025-10-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to family_medical_history table
    op.add_column('family_medical_history', sa.Column('is_deceased', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('family_medical_history', sa.Column('age_at_death', sa.Integer(), nullable=True))
    op.add_column('family_medical_history', sa.Column('cause_of_death', sa.String(500), nullable=True))
    op.add_column('family_medical_history', sa.Column('current_age', sa.Integer(), nullable=True))
    op.add_column('family_medical_history', sa.Column('gender', sa.String(20), nullable=True))
    op.add_column('family_medical_history', sa.Column('chronic_diseases', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    # Make legacy columns nullable for backward compatibility
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

