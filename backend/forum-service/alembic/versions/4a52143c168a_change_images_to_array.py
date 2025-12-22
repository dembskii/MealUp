"""Change images to array

Revision ID: 4a52143c168a
Revises: 0c28c1d41b64
Create Date: 2025-12-22 16:20:12.843497

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '4a52143c168a'
down_revision: Union[str, Sequence[str], None] = '0c28c1d41b64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('posts', 'images')
    
    op.add_column('posts', sa.Column('images', postgresql.ARRAY(sa.TEXT()), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('posts', 'images')
    
    op.add_column('posts', sa.Column('images', sa.VARCHAR(), nullable=True))