"""remove unique constraint from email column

Revision ID: remove_email_unique_constraint
Revises: remove_sender_fields
Create Date: 2025-01-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_email_unique_constraint'
down_revision = 'remove_sender_fields'
branch_labels = None
depends_on = None


def upgrade():
    """Remove unique constraint from email column in users table"""
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Check if users table exists
    if 'users' not in inspector.get_table_names():
        print("Users table does not exist, skipping migration")
        return
    
    # Get existing indexes on users table
    indexes = inspector.get_indexes('users')
    
    # Track if we need to create a new index
    dropped_unique_index = False
    
    # Find and drop the unique index on email column
    for index in indexes:
        if 'email' in index['column_names'] and index.get('unique', False):
            email_index_name = index['name']
            # Drop the unique index
            try:
                op.drop_index(email_index_name, table_name='users')
                print(f"✅ Dropped unique index: {email_index_name}")
                dropped_unique_index = True
            except Exception:
                # Try as constraint instead
                try:
                    op.drop_constraint(email_index_name, 'users', type_='unique')
                    print(f"✅ Dropped unique constraint: {email_index_name}")
                    dropped_unique_index = True
                except Exception as e:
                    print(f"⚠️  Could not drop index/constraint {email_index_name}: {e}")
            break
    
    # If no unique index found in inspector, try common constraint names directly
    if not dropped_unique_index:
        constraint_names = ['ix_users_email', 'users_email_key']
        for constraint_name in constraint_names:
            try:
                op.drop_constraint(constraint_name, 'users', type_='unique')
                print(f"✅ Dropped unique constraint: {constraint_name}")
                dropped_unique_index = True
                break
            except Exception:
                try:
                    op.drop_index(constraint_name, table_name='users')
                    print(f"✅ Dropped unique index: {constraint_name}")
                    dropped_unique_index = True
                    break
                except Exception:
                    continue
    
    # Always try to create non-unique index (will fail gracefully if it already exists)
    try:
        op.create_index('ix_users_email', 'users', ['email'], unique=False)
        print("✅ Created non-unique index on email column")
    except Exception as e:
        error_msg = str(e).lower()
        if 'already exists' in error_msg or 'duplicate' in error_msg:
            print("ℹ️  Non-unique index on email column already exists")
        else:
            print(f"⚠️  Could not create index: {e}")


def downgrade():
    """Re-add unique constraint to email column"""
    # Drop the non-unique index first
    try:
        op.drop_index('ix_users_email', table_name='users')
    except Exception:
        pass
    
    # Re-create unique constraint
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

