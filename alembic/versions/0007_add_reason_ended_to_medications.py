"""add reason_ended to medications

Revision ID: 0007
Revises: 0006
Create Date: 2025-10-12

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade():
    # Get connection to check if column exists
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_columns = [col['name'] for col in inspector.get_columns('medications')]
    
    # Add reason_ended column only if it doesn't exist
    if 'reason_ended' not in existing_columns:
        op.add_column('medications', sa.Column('reason_ended', sa.Text(), nullable=True))


def downgrade():
    # Remove reason_ended column
    op.drop_column('medications', 'reason_ended')

