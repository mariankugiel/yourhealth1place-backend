"""remove current_age and gender from family_medical_history

Revision ID: 0008
Revises: 0007
Create Date: 2025-10-12

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade():
    # Get connection to check if columns exist
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_columns = [col['name'] for col in inspector.get_columns('family_medical_history')]
    
    # Drop current_age column if it exists
    if 'current_age' in existing_columns:
        op.drop_column('family_medical_history', 'current_age')
    
    # Drop gender column if it exists
    if 'gender' in existing_columns:
        op.drop_column('family_medical_history', 'gender')


def downgrade():
    # Add back current_age column
    op.add_column('family_medical_history', sa.Column('current_age', sa.Integer(), nullable=True))
    
    # Add back gender column
    op.add_column('family_medical_history', sa.Column('gender', sa.String(20), nullable=True))

