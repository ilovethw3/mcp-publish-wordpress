"""Fix ArticleStatus enum values mismatch

Revision ID: 1b4ddf359d52
Revises: 9dfe43a9ebd7
Create Date: 2025-08-13 16:14:39.641808

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1b4ddf359d52'
down_revision = '9dfe43a9ebd7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This migration was originally intended to fix ArticleStatus enum values mismatch
    # However, the actual enum issue was resolved in code, not requiring database changes
    # The column type changes from TEXT to AutoString are unnecessary and potentially risky
    # Therefore, this migration is now a no-op to maintain version consistency
    pass


def downgrade() -> None:
    # No operations to reverse as this migration is a no-op
    pass