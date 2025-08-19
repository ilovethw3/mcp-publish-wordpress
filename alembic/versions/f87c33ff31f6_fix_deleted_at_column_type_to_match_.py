"""Fix deleted_at column type to match existing timestamps

Revision ID: f87c33ff31f6
Revises: 4dfb14f91ebe
Create Date: 2025-08-18 20:18:35.624325

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f87c33ff31f6'
down_revision = '4dfb14f91ebe'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Change deleted_at column from timestamp with timezone to timestamp without timezone
    # to match existing created_at and updated_at columns
    op.alter_column('role_templates', 'deleted_at',
                    type_=sa.DateTime(timezone=False),
                    existing_type=sa.DateTime(timezone=True))


def downgrade() -> None:
    # Revert back to timestamp with timezone
    op.alter_column('role_templates', 'deleted_at', 
                    type_=sa.DateTime(timezone=True),
                    existing_type=sa.DateTime(timezone=False))