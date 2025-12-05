"""Create translations table

Revision ID: 0022
Revises: 0021
Create Date: 2025-01-27 14:00:00.000000

This migration creates the translations table to store translations for
user-generated and system-generated content across different languages.

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0022'
down_revision = '0021'
branch_labels = None
depends_on = None


def upgrade():
    """Create translations table"""
    
    # Check if users table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'users' not in inspector.get_table_names():
        print("users table does not exist, skipping migration")
        return
    
    # Create translations table
    op.create_table(
        'translations',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('field_name', sa.String(50), nullable=False),
        sa.Column('language', sa.String(10), nullable=False),
        sa.Column('translated_text', sa.Text(), nullable=False),
        sa.Column('source_language', sa.String(10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('entity_type', 'entity_id', 'field_name', 'language', 
                          name='uq_translations_entity_field_language')
    )
    
    # Create indexes for fast lookups
    op.create_index('idx_translations_lookup', 'translations', 
                   ['entity_type', 'entity_id', 'field_name', 'language'])
    op.create_index('idx_translations_entity', 'translations', 
                   ['entity_type', 'entity_id'])
    op.create_index('idx_translations_language', 'translations', 
                   ['language'])
    op.create_index('idx_translations_entity_type', 'translations', 
                   ['entity_type'])


def downgrade():
    """Drop translations table"""
    
    # Drop indexes first
    op.drop_index('idx_translations_entity_type', table_name='translations')
    op.drop_index('idx_translations_language', table_name='translations')
    op.drop_index('idx_translations_entity', table_name='translations')
    op.drop_index('idx_translations_lookup', table_name='translations')
    
    # Drop table
    op.drop_table('translations')


