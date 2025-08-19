"""Remove primary key and foreign key constraints from role templates

Revision ID: 974a7e6425a1
Revises: f87c33ff31f6
Create Date: 2025-08-18 20:32:42.786261

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '974a7e6425a1'
down_revision = 'f87c33ff31f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Drop foreign key constraints first
    # Drop foreign key from agents table
    op.drop_constraint('agents_role_template_id_fkey', 'agents', type_='foreignkey')
    
    # Drop foreign key from role_template_history table
    op.drop_constraint('role_template_history_role_template_id_fkey', 'role_template_history', type_='foreignkey')
    
    # Step 2: Drop primary key constraints
    # Drop primary key from role_templates table
    op.drop_constraint('role_templates_pkey', 'role_templates', type_='primary')
    
    # Drop primary key from role_template_history table  
    op.drop_constraint('role_template_history_pkey', 'role_template_history', type_='primary')


def downgrade() -> None:
    # Step 1: Recreate primary key constraints
    # Recreate primary key for role_templates
    op.create_primary_key('role_templates_pkey', 'role_templates', ['id'])
    
    # Recreate primary key for role_template_history
    op.create_primary_key('role_template_history_pkey', 'role_template_history', ['id'])
    
    # Step 2: Recreate foreign key constraints
    # Recreate foreign key for role_template_history
    op.create_foreign_key(
        'role_template_history_role_template_id_fkey', 
        'role_template_history', 
        'role_templates', 
        ['role_template_id'], 
        ['id']
    )
    
    # Recreate foreign key for agents
    op.create_foreign_key(
        'agents_role_template_id_fkey',
        'agents', 
        'role_templates', 
        ['role_template_id'], 
        ['id']
    )