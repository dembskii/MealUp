"""Added liked_workouts table

Revision ID: a1b2c3d4e5f6
Revises: cdafdf5ba103
Create Date: 2026-02-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'cdafdf5ba103'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('liked_workouts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('workout_id', sa.VARCHAR(length=255), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'workout_id', name='uq_user_workout_like')
    )
    op.create_index(op.f('ix_liked_workouts_user_id'), 'liked_workouts', ['user_id'], unique=False)
    op.create_index(op.f('ix_liked_workouts_workout_id'), 'liked_workouts', ['workout_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_liked_workouts_workout_id'), table_name='liked_workouts')
    op.drop_index(op.f('ix_liked_workouts_user_id'), table_name='liked_workouts')
    op.drop_table('liked_workouts')
