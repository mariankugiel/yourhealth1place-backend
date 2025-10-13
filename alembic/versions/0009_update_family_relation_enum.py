"""update family relation enum to use Son and Daughter instead of Child

Revision ID: 0009
Revises: 0008
Create Date: 2025-10-12

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade():
    # Update the enum type to add Son and Daughter
    # PostgreSQL doesn't support modifying enums directly, so we need to:
    # 1. Add the new values to the enum
    # 2. Update any existing 'Child' values to 'Son' or 'Daughter' if needed
    
    # Add new enum values
    op.execute("ALTER TYPE familyrelation ADD VALUE IF NOT EXISTS 'Son'")
    op.execute("ALTER TYPE familyrelation ADD VALUE IF NOT EXISTS 'Daughter'")
    
    # Note: We keep 'Child' for backward compatibility with existing data
    # Existing 'Child' entries will still work, new entries can use Son/Daughter


def downgrade():
    # Note: PostgreSQL doesn't support removing enum values
    # So we can't truly downgrade this migration
    # The old enum values (Son, Daughter) will remain in the database
    pass

