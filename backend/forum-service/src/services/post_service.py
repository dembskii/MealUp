from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional, List
from uuid import UUID
import logging

from src.models.post import Post
from src.models.post_like import PostLike
from src.models.post_view import PostView


logger = logging.getLogger(__name__)



class PostService:
    """Service for managing forum posts"""
    
    @staticmethod
    async def get_all_posts(
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[Post]:
        """Retrieve all posts with pagination"""
        try:
            statement = select(Post).offset(skip).limit(limit)
            result = await session.exec(statement)
            posts = result.all()
            logger.info(f"Retrieved {len(posts)} posts (skip={skip}, limit={limit})")
            return posts
        except Exception as e:
            logger.error(f"Error in get_all_posts: {str(e)}")
            return []


    @staticmethod
    async def get_post_by_id(
        session: AsyncSession,
        post_id: UUID
    ) -> Optional[Post]:
        """Retrieve a post by its ID"""
        try:
            statement = select(Post).where(Post.id == post_id)
            result = await session.exec(statement)
            post = result.first()
            if post:
                logger.info(f"Retrieved post with ID: {post_id}")
            else:
                logger.warning(f"No post found with ID: {post_id}")
            return post
        except Exception as e:
            logger.error(f"Error in get_post_by_id: {str(e)}")
            return None


    @staticmethod
    async def create_post(
        session: AsyncSession,
        post_data: dict
    ) -> Optional[Post]:
        """Create a new post"""
        try:
            new_post = Post(**post_data)
            session.add(new_post)
            await session.commit()
            await session.refresh(new_post)
            logger.info(f"Created new post with ID: {new_post.id}")
            return new_post
        except Exception as e:
            logger.error(f"Error in create_post: {str(e)}")
            return None


    @staticmethod
    async def update_post(
        session: AsyncSession,
        post_id: UUID,
        post_data: dict
    ) -> Optional[Post]:
        """Update an existing post"""
        PROTECTED_FIELDS = {"id", "author_id", "created_at", "total_likes", "views_count"}
        try:
            statement = select(Post).where(Post.id == post_id)
            result = await session.exec(statement)
            post = result.first()
            if not post:
                logger.warning(f"No post found with ID: {post_id} for update")
                return None

            for key, value in post_data.items():
                if key not in PROTECTED_FIELDS:
                    setattr(post, key, value)

            session.add(post)
            await session.commit()
            await session.refresh(post)
            logger.info(f"Updated post with ID: {post_id}")
            return post
        except Exception as e:
            logger.error(f"Error in update_post: {str(e)}")
            return None


    @staticmethod
    async def delete_post(
        session: AsyncSession,
        post_id: UUID
    ) -> bool:
        """Delete a post by its ID"""
        try:
            statement = select(Post).where(Post.id == post_id)
            result = await session.exec(statement)
            post = result.first()
            if not post:
                logger.warning(f"No post found with ID: {post_id} for deletion")
                return False

            await session.delete(post)
            await session.commit()
            logger.info(f"Deleted post with ID: {post_id}")
            return True
        except Exception as e:
            logger.error(f"Error in delete_post: {str(e)}")
            return False