from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID
import logging
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import func

from src.models.comment import Comment
from src.models.comment_like import CommentLike
from src.models.post import Post


logger = logging.getLogger(__name__)


class CommentService:
    """Service for managing comments"""

    @staticmethod
    async def create_comment(
        session: AsyncSession,
        post_id: UUID,
        author_id: UUID,
        content: str,
        parent_comment_id: Optional[UUID] = None
    ) -> Optional[Comment]:
        """Create a new comment"""
        try:
            post_statement = select(Post).where(Post.id == post_id)
            post_result = await session.exec(post_statement)
            post = post_result.first()
            
            if not post:
                logger.warning(f"Post {post_id} not found")
                return None
            
            # Verify parent comment exists if provided
            if parent_comment_id:
                parent_statement = select(Comment).where(Comment.id == parent_comment_id)
                parent_result = await session.exec(parent_statement)
                parent_comment = parent_result.first()
                
                if not parent_comment:
                    logger.warning(f"Parent comment {parent_comment_id} not found")
                    return None
                
                if parent_comment.post_id != post_id:
                    logger.warning(f"Parent comment {parent_comment_id} does not belong to post {post_id}")
                    return None
            
            # Create comment
            comment = Comment(
                author_id=author_id,
                content=content,
                post_id=post_id,
                parent_comment_id=parent_comment_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            session.add(comment)
            await session.commit()
            await session.refresh(comment)
            
            logger.info(f"Created comment {comment.id} for post {post_id}")
            return comment
            
        except Exception as e:
            logger.error(f"Error creating comment: {str(e)}")
            await session.rollback()
            return None



    @staticmethod
    async def get_comment_by_id(
        session: AsyncSession,
        comment_id: UUID
    ) -> Optional[Comment]:
        """Get a single comment by ID"""
        try:
            statement = select(Comment).where(Comment.id == comment_id)
            result = await session.exec(statement)
            comment = result.first()
            
            if comment:
                logger.info(f"Retrieved comment {comment_id}")
            else:
                logger.warning(f"Comment {comment_id} not found")
            
            return comment
            
        except Exception as e:
            logger.error(f"Error retrieving comment {comment_id}: {str(e)}")
            return None



    @staticmethod
    async def get_comments_by_post(
        session: AsyncSession,
        post_id: UUID,
        skip: int = 0,
        limit: int = 50
    ) -> List[Comment]:
        """Get all top-level comments for a post (without parent)"""
        try:
            post_statement = select(Post).where(Post.id == post_id)
            post_result = await session.exec(post_statement)
            post = post_result.first()
            
            if not post:
                logger.warning(f"Post {post_id} not found")
                return []
            
            statement = (
                select(Comment)
                .where(Comment.post_id == post_id, Comment.parent_comment_id.is_(None))
                .order_by(Comment.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await session.exec(statement)
            comments = result.all()
            
            logger.info(f"Retrieved {len(comments)} top-level comments for post {post_id}")
            return list(comments)
            
        except Exception as e:
            logger.error(f"Error retrieving comments for post {post_id}: {str(e)}")
            return []



    @staticmethod
    async def get_comment_replies(
        session: AsyncSession,
        parent_comment_id: UUID,
        skip: int = 0,
        limit: int = 50
    ) -> List[Comment]:
        """Get direct replies to a comment"""
        try:
            statement = (
                select(Comment)
                .where(Comment.parent_comment_id == parent_comment_id)
                .order_by(Comment.created_at.asc())
                .offset(skip)
                .limit(limit)
            )
            result = await session.exec(statement)
            replies = result.all()
            
            logger.info(f"Retrieved {len(replies)} replies for comment {parent_comment_id}")
            return list(replies)
            
        except Exception as e:
            logger.error(f"Error retrieving replies for comment {parent_comment_id}: {str(e)}")
            return []



    @staticmethod
    async def get_comments_tree(
        session: AsyncSession,
        post_id: UUID,
        max_depth: int = 3
    ) -> List[dict]:
        """Get comments with nested replies in tree structure"""
        try:
            statement = (
                select(Comment)
                .where(Comment.post_id == post_id)
                .order_by(Comment.created_at.asc())
            )
            result = await session.exec(statement)
            all_comments = result.all()
            
            comments_dict = {str(comment.id): comment for comment in all_comments}
            
            def build_tree(parent_id: Optional[str], depth: int = 0) -> List[dict]:
                if depth >= max_depth:
                    return []
                
                children = []
                for comment in all_comments:
                    comment_parent = str(comment.parent_comment_id) if comment.parent_comment_id else None
                    if comment_parent == parent_id:
                        comment_dict = {
                            "comment": comment,
                            "replies": build_tree(str(comment.id), depth + 1)
                        }
                        children.append(comment_dict)
                
                return children
            
            tree = build_tree(None)
            logger.info(f"Built comment tree for post {post_id} with {len(tree)} top-level comments")
            return tree
            
        except Exception as e:
            logger.error(f"Error building comment tree for post {post_id}: {str(e)}")
            return []



    @staticmethod
    async def update_comment(
        session: AsyncSession,
        comment_id: UUID,
        author_id: UUID,
        content: str
    ) -> Optional[Comment]:
        """Update a comment"""
        try:
            statement = select(Comment).where(Comment.id == comment_id)
            result = await session.exec(statement)
            comment = result.first()
            
            if not comment:
                logger.warning(f"Comment {comment_id} not found")
                return None

            if comment.author_id != author_id:
                logger.warning(f"User {author_id} is not the author of comment {comment_id}")
                return None
            
            comment.content = content
            comment.updated_at = datetime.now(timezone.utc)
            
            session.add(comment)
            await session.commit()
            await session.refresh(comment)
            
            logger.info(f"Updated comment {comment_id}")
            return comment
            
        except Exception as e:
            logger.error(f"Error updating comment {comment_id}: {str(e)}")
            await session.rollback()
            return None



    @staticmethod
    async def delete_comment(
        session: AsyncSession,
        comment_id: UUID,
        author_id: UUID
    ) -> bool:
        """Delete a comment and all its replies"""
        try:
            statement = select(Comment).where(Comment.id == comment_id)
            result = await session.exec(statement)
            comment = result.first()
            
            if not comment:
                logger.warning(f"Comment {comment_id} not found")
                return False
            
            if comment.author_id != author_id:
                logger.warning(f"User {author_id} is not the author of comment {comment_id}")
                return False
            
            await CommentService._delete_comment_recursive(session, comment_id)
            
            await session.commit()
            logger.info(f"Deleted comment {comment_id} and all its replies")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting comment {comment_id}: {str(e)}")
            await session.rollback()
            return False



    @staticmethod
    async def _delete_comment_recursive(
        session: AsyncSession,
        comment_id: UUID
    ):
        """Recursively delete a comment and all its replies"""
        statement = select(Comment).where(Comment.parent_comment_id == comment_id)
        result = await session.exec(statement)
        replies = result.all()
        
        for reply in replies:
            await CommentService._delete_comment_recursive(session, reply.id)
        
        likes_statement = select(CommentLike).where(CommentLike.comment_id == comment_id)
        likes_result = await session.exec(likes_statement)
        likes = likes_result.all()
        for like in likes:
            await session.delete(like)
        
        comment_statement = select(Comment).where(Comment.id == comment_id)
        comment_result = await session.exec(comment_statement)
        comment = comment_result.first()
        if comment:
            await session.delete(comment)



    @staticmethod
    async def get_comments_count_by_post(
        session: AsyncSession,
        post_id: UUID
    ) -> int:
        """Get total comment count for a post (including all nested replies)"""
        try:
            statement = select(func.count(Comment.id)).where(Comment.post_id == post_id)
            result = await session.exec(statement)
            count = result.first() or 0
            logger.info(f"Post {post_id} has {count} total comments")
            return count
            
        except Exception as e:
            logger.error(f"Error getting comments count for post {post_id}: {str(e)}")
            return 0