"""Create initial tables

Revision ID: 001
Revises: 
Create Date: 2025-08-11 15:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### Create initial tables ###
    
    # Create articles table
    op.create_table('articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column('content_markdown', sa.Text(), nullable=False),
        sa.Column('tags', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column('category', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column('status', sa.Enum('pending_review', 'publishing', 'published', 'publish_failed', 'rejected', name='articlestatus'), nullable=False),
        sa.Column('submitted_by', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reviewed_by', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('wordpress_post_id', sa.Integer(), nullable=True),
        sa.Column('wordpress_url', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('publish_error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_articles_status'), 'articles', ['status'], unique=False)
    op.create_index(op.f('ix_articles_submitted_by'), 'articles', ['submitted_by'], unique=False)
    op.create_index(op.f('ix_articles_submitted_at'), 'articles', ['submitted_at'], unique=False)

    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('hashed_password', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('full_name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)


def downgrade() -> None:
    # ### Drop tables ###
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_articles_submitted_at'), table_name='articles')
    op.drop_index(op.f('ix_articles_submitted_by'), table_name='articles')
    op.drop_index(op.f('ix_articles_status'), table_name='articles')
    op.drop_table('articles')