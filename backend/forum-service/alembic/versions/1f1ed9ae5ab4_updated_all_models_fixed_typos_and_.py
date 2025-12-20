"""Updated all models, fixed typos and refactored timestamps for created_at and updated_at to save time of creation in proper way independently from timezone where record is created.

Revision ID: 1f1ed9ae5ab4
Revises: 1a8808feff76
Create Date: 2025-12-20 16:15:30.526841

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f1ed9ae5ab4'
down_revision: Union[str, Sequence[str], None] = '1a8808feff76'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint('comments_post_uid_fkey', 'comments', type_='foreignkey')
    op.drop_constraint('post_likes_post_uid_fkey', 'post_likes', type_='foreignkey')
    op.drop_constraint('post_views_post_uid_fkey', 'post_views', type_='foreignkey')
    
    op.alter_column('posts', 'uid', new_column_name='id')
    
    op.alter_column('comments', 'post_uid', new_column_name='post_id')
    op.create_foreign_key('comments_post_id_fkey', 'comments', 'posts', ['post_id'], ['id'])
    
    op.alter_column('post_likes', 'post_uid', new_column_name='post_id')
    op.create_unique_constraint('uq_user_post_like', 'post_likes', ['user_id', 'post_id'])
    op.create_foreign_key('post_likes_post_id_fkey', 'post_likes', 'posts', ['post_id'], ['id'])
    
    op.alter_column('post_views', 'post_uid', new_column_name='post_id')
    op.create_foreign_key('post_views_post_id_fkey', 'post_views', 'posts', ['post_id'], ['id'])
    
    op.create_unique_constraint('uq_user_comment_like', 'comment_likes', ['user_id', 'comment_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_user_comment_like', 'comment_likes', type_='unique')
    
    op.drop_constraint('post_views_post_id_fkey', 'post_views', type_='foreignkey')
    op.alter_column('post_views', 'post_id', new_column_name='post_uid')
    op.create_foreign_key('post_views_post_uid_fkey', 'post_views', 'posts', ['post_uid'], ['id'])
    
    op.drop_constraint('post_likes_post_id_fkey', 'post_likes', type_='foreignkey')
    op.drop_constraint('uq_user_post_like', 'post_likes', type_='unique')
    op.alter_column('post_likes', 'post_id', new_column_name='post_uid')
    op.create_foreign_key('post_likes_post_uid_fkey', 'post_likes', 'posts', ['post_uid'], ['id'])
    
    op.drop_constraint('comments_post_id_fkey', 'comments', type_='foreignkey')
    op.alter_column('comments', 'post_id', new_column_name='post_uid')
    op.create_foreign_key('comments_post_uid_fkey', 'comments', 'posts', ['post_uid'], ['uid'])
    
    op.alter_column('posts', 'id', new_column_name='uid')