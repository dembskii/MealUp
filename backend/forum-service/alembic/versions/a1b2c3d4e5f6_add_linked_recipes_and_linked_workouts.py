"""Add linked_recipes and linked_workouts to posts

Revision ID: a1b2c3d4e5f6
Revises: e6beaaaee0c6
Create Date: 2026-02-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'e6beaaaee0c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add linked_recipes and linked_workouts columns to posts table."""
    op.add_column('posts', sa.Column('linked_recipes', postgresql.ARRAY(sa.TEXT()), nullable=True))
    op.add_column('posts', sa.Column('linked_workouts', postgresql.ARRAY(sa.TEXT()), nullable=True))


def downgrade() -> None:
    """Remove linked_recipes and linked_workouts columns from posts table."""
    op.drop_column('posts', 'linked_workouts')
    op.drop_column('posts', 'linked_recipes')
