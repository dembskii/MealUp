from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional, List
from uuid import UUID
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import func

from src.models.post import Post
from src.models.post_view import PostView
from src.models.post_like import PostLike
from src.models.comment import Comment
from src.models.comment_like import CommentLike
from src.services.comment_service import CommentService


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
        """Delete a post by its ID, including all related records"""
        try:
            statement = select(Post).where(Post.id == post_id)
            result = await session.exec(statement)
            post = result.first()
            if not post:
                logger.warning(f"No post found with ID: {post_id} for deletion")
                return False

            # 1. Find all comment IDs for this post
            comment_stmt = select(Comment.id).where(Comment.post_id == post_id)
            comment_result = await session.exec(comment_stmt)
            comment_ids = comment_result.all()

            # 2. Delete CommentLikes for those comments
            if comment_ids:
                for cid in comment_ids:
                    cl_stmt = select(CommentLike).where(CommentLike.comment_id == cid)
                    cl_result = await session.exec(cl_stmt)
                    for cl in cl_result.all():
                        await session.delete(cl)

            # 3. Delete Comments
            if comment_ids:
                for cid in comment_ids:
                    c_stmt = select(Comment).where(Comment.id == cid)
                    c_result = await session.exec(c_stmt)
                    comment = c_result.first()
                    if comment:
                        await session.delete(comment)

            # 4. Delete PostLikes
            pl_stmt = select(PostLike).where(PostLike.post_id == post_id)
            pl_result = await session.exec(pl_stmt)
            for pl in pl_result.all():
                await session.delete(pl)

            # 5. Delete PostViews
            pv_stmt = select(PostView).where(PostView.post_id == post_id)
            pv_result = await session.exec(pv_stmt)
            for pv in pv_result.all():
                await session.delete(pv)

            # 6. Delete the Post itself
            await session.delete(post)
            await session.commit()
            logger.info(f"Deleted post with ID: {post_id} and all related records")
            return True
        except Exception as e:
            logger.error(f"Error in delete_post: {str(e)}")
            await session.rollback()
            return False



    @staticmethod
    async def track_post_view(
        session: AsyncSession,
        post_id: UUID,
        user_id: Optional[UUID] = None,
        engagement_seconds: Optional[int] = None
    ) -> bool:
        """Track a post view"""
        try:
            # Create PostView record
            view = PostView(
                post_id=post_id,
                user_id=user_id,
                viewed_at=datetime.now(timezone.utc),
                engagement_seconds=engagement_seconds
            )
            session.add(view)
            await session.commit()

            # Increment views_count on post
            statement = select(Post).where(Post.id == post_id)
            result = await session.exec(statement)
            post = result.first()
            
            if post:
                post.views_count += 1
                session.add(post)
                await session.commit()
                logger.info(f"Tracked view for post {post_id}, total views: {post.views_count}")
                return True
            else:
                logger.warning(f"Post {post_id} not found for view tracking")
                return False
                
        except Exception as e:
            logger.error(f"Error tracking post view: {str(e)}")
            await session.rollback()
            return False



    @staticmethod
    async def calculate_trending_coefficient(
        session: AsyncSession,
        post_id: UUID
    ) -> Optional[float]:
        """
        Calculate trending coefficient based on:
        - Likes (weight: 5)
        - Views (weight: 1)
        - Comments (weight: 3)
        - Time decay (posts older than 7 days get lower score)
        """
        try:
            statement = select(Post).where(Post.id == post_id)
            result = await session.exec(statement)
            post = result.first()
            
            if not post:
                logger.warning(f"Post {post_id} not found for trending calculation")
                return None
            
            # Get counts
            likes_count = post.total_likes
            views_count = post.views_count
            
            # ZMIENIONE: Używamy CommentService zamiast bezpośredniego zapytania
            comments_count = await CommentService.get_comments_count_by_post(
                session=session,
                post_id=post_id
            )
            
            # Calculate age in days
            age_days = (datetime.now(timezone.utc) - post.created_at).days
            
            # Time decay factor (exponential decay)
            # Posts lose 50% value after 7 days
            time_decay = 0.5 ** (age_days / 7.0)
            
            # Calculate weighted score
            engagement_score = (
                (likes_count * 5) +
                (views_count * 1) +
                (comments_count * 3)
            )
            
            # Apply time decay
            trending_coefficient = engagement_score * time_decay
            
            # Update post
            post.trending_coefficient = trending_coefficient
            session.add(post)
            await session.commit()
            
            logger.info(
                f"Updated trending coefficient for post {post_id}: {trending_coefficient:.2f} "
                f"(likes={likes_count}, views={views_count}, comments={comments_count}, age={age_days}d)"
            )
            
            return trending_coefficient
            
        except Exception as e:
            logger.error(f"Error calculating trending coefficient: {str(e)}")
            await session.rollback()
            return None



    @staticmethod
    async def get_trending_posts(
        session: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        min_coefficient: float = 0.0
    ) -> List[Post]:
        """Get posts sorted by trending coefficient"""
        try:
            statement = (
                select(Post)
                .where(Post.trending_coefficient >= min_coefficient)
                .order_by(Post.trending_coefficient.desc())
                .offset(skip)
                .limit(limit)
            )
            result = await session.exec(statement)
            posts = result.all()
            logger.info(f"Retrieved {len(posts)} trending posts")
            return posts
        except Exception as e:
            logger.error(f"Error getting trending posts: {str(e)}")
            return []



    @staticmethod
    async def get_post_views_count(
        session: AsyncSession,
        post_id: UUID,
        hours: Optional[int] = None
    ) -> int:
        """Get view count for a post, optionally filtered by time"""
        try:
            exist = select(Post).where(Post.id == post_id)
            result = await session.exec(exist)
            post = result.first()
            if not post:
                logger.warning(f"Post {post_id} not found when getting views count")
                return None

            statement = select(func.count(PostView.id)).where(PostView.post_id == post_id)

            if hours:
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
                statement = statement.where(PostView.viewed_at >= cutoff_time)

            result = await session.exec(statement)
            count = result.first() or 0
            logger.info(f"Post {post_id} has {count} views" + (f" in last {hours}h" if hours else ""))
            return count
        except Exception as e:
            logger.error(f"Error getting post views count: {str(e)}")
            return None



    @staticmethod
    async def recalculate_all_trending_coefficients(
        session: AsyncSession
    ) -> int:
        """Recalculate trending coefficients for all posts (background task)"""
        try:
            statement = select(Post)
            result = await session.exec(statement)
            posts = result.all()
            
            updated_count = 0
            for post in posts:
                coefficient = await PostService.calculate_trending_coefficient(session, post.id)
                if coefficient is not None:
                    updated_count += 1
            
            logger.info(f"Recalculated trending coefficients for {updated_count} posts")
            return updated_count
        except Exception as e:
            logger.error(f"Error recalculating trending coefficients: {str(e)}")
            return 0