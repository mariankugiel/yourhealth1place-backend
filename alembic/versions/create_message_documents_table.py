"""create_message_documents_table

Revision ID: create_message_documents_table
Revises: 4db4dbe49920
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'create_message_documents_table'
down_revision = '0019'
branch_labels = None
depends_on = None


def upgrade():
    # Create message_documents table
    op.create_table('message_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('original_file_name', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_extension', sa.String(length=10), nullable=False),
        sa.Column('s3_bucket', sa.String(length=100), nullable=False),
        sa.Column('s3_key', sa.String(length=500), nullable=False),
        sa.Column('s3_url', sa.Text(), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_message_documents_message_id', 'message_documents', ['message_id'])
    op.create_index('idx_message_documents_uploaded_by', 'message_documents', ['uploaded_by'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_message_documents_uploaded_by', table_name='message_documents')
    op.drop_index('idx_message_documents_message_id', table_name='message_documents')
    
    # Drop table
    op.drop_table('message_documents')
