"""Change diagnosed_date and resolved_date from DateTime to Date type

Revision ID: 0017
Revises: 0016
Create Date: 2025-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0017'
down_revision = '0016'
branch_labels = None
depends_on = None


def upgrade():
    # Change diagnosed_date from DateTime to Date
    op.alter_column('medical_conditions', 'diagnosed_date',
                    existing_type=postgresql.TIMESTAMP(),
                    type_=sa.Date(),
                    existing_nullable=True)
    
    # Change resolved_date from DateTime to Date
    op.alter_column('medical_conditions', 'resolved_date',
                    existing_type=postgresql.TIMESTAMP(),
                    type_=sa.Date(),
                    existing_nullable=True)


def downgrade():
    # Revert diagnosed_date from Date to DateTime
    op.alter_column('medical_conditions', 'diagnosed_date',
                    existing_type=sa.Date(),
                    type_=postgresql.TIMESTAMP(),
                    existing_nullable=True)
    
    # Revert resolved_date from Date to DateTime
    op.alter_column('medical_conditions', 'resolved_date',
                    existing_type=sa.Date(),
                    type_=postgresql.TIMESTAMP(),
                    existing_nullable=True)
