"""Add internal primary keys and make id non-unique

Revision ID: 3b3847264444
Revises: 974a7e6425a1
Create Date: 2025-08-18 21:39:11.563685

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3b3847264444'
down_revision = '974a7e6425a1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add internal_id column as serial primary key
    op.execute("ALTER TABLE role_templates ADD COLUMN internal_id SERIAL")
    op.create_primary_key('role_templates_pkey', 'role_templates', ['internal_id'])
    
    # For role_template_history, just recreate its primary key constraint
    op.create_primary_key('role_template_history_pkey', 'role_template_history', ['id'])


def downgrade() -> None:
    # Drop primary key constraints
    op.drop_constraint('role_templates_pkey', 'role_templates', type_='primary')
    op.drop_constraint('role_template_history_pkey', 'role_template_history', type_='primary')
    
    # Drop the internal_id column (this will also drop the sequence)
    op.drop_column('role_templates', 'internal_id')