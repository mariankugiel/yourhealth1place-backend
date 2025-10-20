"""Remove current_value column from health_goals table

Revision ID: 0012
Revises: 0011
Create Date: 2025-01-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0012'
down_revision = '0011'
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    
    # Check if current_value column exists before dropping it
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'health_goals' AND column_name = 'current_value'
    """))
    
    if result.fetchone():
        op.drop_column('health_goals', 'current_value')
        print("Dropped current_value column from health_goals table")


def downgrade():
    # Add the current_value column back
    op.add_column('health_goals', sa.Column('current_value', postgresql.JSON(astext_type=sa.Text()), nullable=True))
