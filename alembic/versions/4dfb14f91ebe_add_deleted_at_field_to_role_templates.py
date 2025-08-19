"""add_deleted_at_field_to_role_templates

Revision ID: 4dfb14f91ebe
Revises: 4ab0d0f15b57
Create Date: 2025-08-18 20:12:04.897229

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4dfb14f91ebe'
down_revision = '4ab0d0f15b57'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add deleted_at column to role_templates table for logical deletion
    op.add_column('role_templates', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    
    # Create index on deleted_at for performance
    op.create_index('ix_role_templates_deleted_at', 'role_templates', ['deleted_at'])


def downgrade() -> None:
    # Remove index and column in reverse order
    op.drop_index('ix_role_templates_deleted_at', table_name='role_templates')
    op.drop_column('role_templates', 'deleted_at')