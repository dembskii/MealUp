from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID
import logging
from datetime import datetime, timezone
from sqlalchemy import func

from src.models.post import Post
from src.models.post_like import PostLike
from src.models.comment import Comment


logger = logging.getLogger(__name__)



class LikeService:
    @staticmethod
    async def track_post_like(
        session: AsyncSession,
        post_id: UUID,
        user_id: UUID
    ) -> bool:
        """Track a post like"""
        try:
            # Check if user already liked the post
            statement = select(PostLike).where(
                PostLike.post_id == post_id,
                PostLike.user_id == user_id
            )
            result = await session.exec(statement)
            existing_like = result.first()
            
            if existing_like:
                logger.info(f"User {user_id} already liked post {post_id}")
                return False

            # Create PostLike record
            like = PostLike(
                post_id=post_id,
                user_id=user_id,
                liked_at=datetime.now(timezone.utc)
            )
            session.add(like)
            await session.commit()

            # Increment total_likes on post
            post_statement = select(Post).where(Post.id == post_id)
            post_result = await session.exec(post_statement)
            post = post_result.first()
            
            if post:
                post.total_likes += 1
                session.add(post)
                await session.commit()
                logger.info(f"User {user_id} liked post {post_id}, total likes: {post.total_likes}")
                return True
            else:
                logger.warning(f"Post {post_id} not found for like tracking")
                return False
                
        except Exception as e:
            logger.error(f"Error tracking post like: {str(e)}")
            await session.rollback()
            return False



    @staticmethod
    async def get_post_likes_count(
        session: AsyncSession,
        post_id: UUID
    ) -> int:
        """Get like count for a post"""
        try:
            exist = select(Post).where(Post.id == post_id)
            result = await session.exec(exist)
            post = result.first()

            if not post:
                logger.warning(f"Post {post_id} not found when getting likes count")
                return None
            
            statement = select(func.count(PostLike.id)).where(PostLike.post_id == post_id)
            result = await session.exec(statement)
            count = result.first() or 0
            logger.info(f"Post {post_id} has {count} likes")
            return count
        except Exception as e:
            logger.error(f"Error getting post likes count: {str(e)}")
            return None