from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID
import logging
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import func

from src.models.post import Post
from src.models.post_like import PostLike
from src.models.comment import Comment
from src.models.comment_like import CommentLike



logger = logging.getLogger(__name__)



class LikeService:
    #================= Track Post Like ==================#
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

            post_statement = select(Post).where(Post.id == post_id)
            post_result = await session.exec(post_statement)
            post = post_result.first()
            
            if not post:
                logger.warning(f"Post {post_id} not found for like tracking")
                return False

            like = PostLike(
                post_id=post_id,
                user_id=user_id,
                created_at=datetime.now(timezone.utc)
            )
            session.add(like)
            
            post.total_likes += 1
            session.add(post)
            
            await session.commit()
            
            logger.info(f"User {user_id} liked post {post_id}, total likes: {post.total_likes}")
            return True
                
        except Exception as e:
            logger.error(f"Error tracking post like: {str(e)}")
            await session.rollback()
            return False



    @staticmethod
    async def track_post_unlike(
        session: AsyncSession,
        post_id: UUID,
        user_id: UUID
    ) -> bool:
        """Remove a post like (unlike)"""
        try:
            statement = select(PostLike).where(
                PostLike.post_id == post_id,
                PostLike.user_id == user_id
            )
            result = await session.exec(statement)
            existing_like = result.first()
            
            if not existing_like:
                logger.info(f"User {user_id} has not liked post {post_id}")
                return False

            post_statement = select(Post).where(Post.id == post_id)
            post_result = await session.exec(post_statement)
            post = post_result.first()
            
            if not post:
                logger.warning(f"Post {post_id} not found for unlike tracking")
                return False

            await session.delete(existing_like)
            post.total_likes = max(0, post.total_likes - 1)
            session.add(post)
            
            await session.commit()
            
            logger.info(f"User {user_id} unliked post {post_id}, total likes: {post.total_likes}")
            return True
                
        except Exception as e:
            logger.error(f"Error tracking post unlike: {str(e)}")
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



    #================= Track Comment Like ==================#
    @staticmethod
    async def track_comment_like(
        session: AsyncSession,
        comment_id: UUID,
        user_id: UUID
    ) -> bool:
        """Track a comment like"""
        try:
            statement = select(CommentLike).where(
                CommentLike.comment_id == comment_id,
                CommentLike.user_id == user_id
            )
            result = await session.exec(statement)
            existing_like = result.first()
            
            if existing_like:
                logger.info(f"User {user_id} already liked comment {comment_id}")
                return False

            comment_statement = select(Comment).where(Comment.id == comment_id)
            comment_result = await session.exec(comment_statement)
            comment = comment_result.first()
            
            if not comment:
                logger.warning(f"Comment {comment_id} not found")
                return False
            
            like = CommentLike(
                comment_id=comment_id,
                user_id=user_id,
                created_at=datetime.now(timezone.utc)
            )
            session.add(like)

            comment.total_likes += 1
            session.add(comment)
            
            await session.commit()
            logger.info(f"User {user_id} liked comment {comment_id}, total likes: {comment.total_likes}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking comment like: {str(e)}")
            await session.rollback()
            return False



    @staticmethod
    async def remove_comment_like(
        session: AsyncSession,
        comment_id: UUID,
        user_id: UUID
    ) -> bool:
        """Remove a comment like"""
        try:
            # Find existing like
            statement = select(CommentLike).where(
                CommentLike.comment_id == comment_id,
                CommentLike.user_id == user_id
            )
            result = await session.exec(statement)
            existing_like = result.first()
            
            if not existing_like:
                logger.info(f"User {user_id} has not liked comment {comment_id}")
                return False
            
            comment_statement = select(Comment).where(Comment.id == comment_id)
            comment_result = await session.exec(comment_statement)
            comment = comment_result.first()
            
            if not comment:
                logger.warning(f"Comment {comment_id} not found")
                return False
            
            await session.delete(existing_like)
            
            comment.total_likes = max(0, (comment.total_likes or 0) - 1)
            session.add(comment)
            
            await session.commit()

            logger.info(f"User {user_id} unliked comment {comment_id}, total likes: {comment.total_likes}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing comment like: {str(e)}")
            await session.rollback()
            return False



    @staticmethod
    async def get_comment_likes_count(
        session: AsyncSession,
        comment_id: UUID
    ) -> Optional[int]:
        """Get like count for a comment"""
        try:
            exist = select(Comment).where(Comment.id == comment_id)
            result = await session.exec(exist)
            comment = result.first()

            if not comment:
                logger.warning(f"Comment {comment_id} not found when getting likes count")
                return None
            
            statement = select(func.count(CommentLike.id)).where(CommentLike.comment_id == comment_id)
            result = await session.exec(statement)
            count = result.first() or 0
            logger.info(f"Comment {comment_id} has {count} likes")
            return count
            
        except Exception as e:
            logger.error(f"Error getting comment likes count: {str(e)}")
            return None