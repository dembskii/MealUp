from sqlmodel import select, text
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import func, desc, or_, and_, cast, String
from sqlalchemy.dialects.postgresql import ARRAY
from typing import Optional, List, Tuple
from uuid import UUID
import logging
import httpx
from datetime import datetime, timezone

from src.models.post import Post
from src.models.comment import Comment
from src.validators.search import (
    SearchQuery, SearchCategory, SearchSortBy,
    PostSearchResult, AuthorSearchResult, 
    RecipeSearchResult, WorkoutSearchResult,
    SearchResponse, TagSuggestion, SearchSuggestionsResponse
)
from src.core.config import settings


logger = logging.getLogger(__name__)



class SearchService:
    """Service for full-text search across forum content"""
    
    RECIPE_SERVICE_URL = settings.RECIPE_SERVICE_URL
    WORKOUT_SERVICE_URL = settings.WORKOUT_SERVICE_URL
    
    @staticmethod
    async def search(
        session: AsyncSession,
        search_query: SearchQuery,
        auth_token: Optional[str] = None
    ) -> SearchResponse:
        """
        Perform full-text search across all categories or specific category.
        Uses PostgreSQL full-text search for posts and external APIs for recipes/workouts.
        """
        try:
            posts: List[PostSearchResult] = []
            recipes: List[RecipeSearchResult] = []
            workouts: List[WorkoutSearchResult] = []
            authors: List[AuthorSearchResult] = []
            
            query = search_query.query.strip()
            category = search_query.category
            
            # Search posts
            if category in [SearchCategory.ALL, SearchCategory.POSTS]:
                posts = await SearchService._search_posts(
                    session=session,
                    query=query,
                    tags=search_query.tags,
                    author_id=search_query.author_id,
                    sort_by=search_query.sort_by,
                    skip=search_query.skip,
                    limit=search_query.limit
                )
            
            # Search authors
            if category in [SearchCategory.ALL, SearchCategory.AUTHORS]:
                authors = await SearchService._search_authors(
                    session=session,
                    query=query,
                    skip=search_query.skip,
                    limit=search_query.limit
                )
            
            # Search recipes (external service)
            if category in [SearchCategory.ALL, SearchCategory.RECIPES]:
                recipes = await SearchService._search_recipes(
                    query=query,
                    tags=search_query.tags,
                    skip=search_query.skip,
                    limit=search_query.limit,
                    auth_token=auth_token
                )
            
            # Search workouts (external service)
            if category in [SearchCategory.ALL, SearchCategory.WORKOUTS]:
                workouts = await SearchService._search_workouts(
                    query=query,
                    tags=search_query.tags,
                    skip=search_query.skip,
                    limit=search_query.limit,
                    auth_token=auth_token
                )
            
            total_results = len(posts) + len(recipes) + len(workouts) + len(authors)
            has_more = (
                len(posts) == search_query.limit or
                len(recipes) == search_query.limit or
                len(workouts) == search_query.limit or
                len(authors) == search_query.limit
            )
            
            logger.info(
                f"Search completed: query='{query}', category={category}, "
                f"posts={len(posts)}, recipes={len(recipes)}, "
                f"workouts={len(workouts)}, authors={len(authors)}"
            )
            
            return SearchResponse(
                query=query,
                category=category,
                total_results=total_results,
                posts=posts,
                recipes=recipes,
                workouts=workouts,
                authors=authors,
                has_more=has_more
            )
            
        except Exception as e:
            logger.error(f"Error in search: {str(e)}", exc_info=True)
            return SearchResponse(
                query=search_query.query,
                category=search_query.category,
                total_results=0
            )



    @staticmethod
    async def _search_posts(
        session: AsyncSession,
        query: str,
        tags: Optional[List[str]] = None,
        author_id: Optional[str] = None,
        sort_by: SearchSortBy = SearchSortBy.RELEVANCE,
        skip: int = 0,
        limit: int = 20
    ) -> List[PostSearchResult]:
        """
        Search posts using PostgreSQL ILIKE search.
        """
        try:
            like_query = f"%{query}%"
            
            # Budujemy zapytanie dynamicznie
            conditions = []
            
            # Bazowe wyszukiwanie tekstowe
            base_condition = or_(
                Post.title.ilike(like_query),
                Post.content.ilike(like_query)
            )
            conditions.append(base_condition)
            
            # Tag filter
            if tags:
                # Sprawdź czy post ma przynajmniej jeden z tagów
                tag_conditions = [Post.tags.contains([tag]) for tag in tags]
                conditions.append(or_(*tag_conditions))
            
            # Author filter
            if author_id:
                try:
                    author_uuid = UUID(author_id)
                    conditions.append(Post.author_id == author_uuid)
                except ValueError:
                    logger.warning(f"Invalid author_id format: {author_id}")
            
            # Buduj zapytanie
            statement = select(Post).where(and_(*conditions))
            
            # Sortowanie
            if sort_by == SearchSortBy.NEWEST:
                statement = statement.order_by(desc(Post.created_at))
            elif sort_by == SearchSortBy.TRENDING:
                statement = statement.order_by(desc(Post.trending_coefficient), desc(Post.created_at))
            elif sort_by == SearchSortBy.MOST_LIKED:
                statement = statement.order_by(desc(Post.total_likes), desc(Post.created_at))
            else:
                statement = statement.order_by(desc(Post.created_at))
            
            # Paginacja
            statement = statement.offset(skip).limit(limit)
            
            # Wykonaj zapytanie
            result = await session.exec(statement)
            posts_db = result.all()
            
            logger.info(f"Found {len(posts_db)} posts for query '{query}'")
            
            # Konwertuj na PostSearchResult
            posts = []
            for post in posts_db:
                # Pobierz liczbę komentarzy
                comment_stmt = select(func.count(Comment.id)).where(Comment.post_id == post.id)
                comment_result = await session.exec(comment_stmt)
                comments_count = comment_result.first() or 0
                
                posts.append(PostSearchResult(
                    id=str(post.id),
                    title=post.title,
                    content=(post.content[:500] if post.content else ""),
                    author_id=str(post.author_id),
                    tags=list(post.tags) if post.tags else [],
                    images=list(post.images) if post.images else [],
                    total_likes=post.total_likes or 0,
                    views_count=post.views_count or 0,
                    comments_count=comments_count,
                    trending_coefficient=float(post.trending_coefficient or 0),
                    created_at=post.created_at,
                    updated_at=post.updated_at,
                    relevance_score=1.0
                ))
            
            return posts
            
        except Exception as e:
            logger.error(f"Error in _search_posts: {str(e)}", exc_info=True)
            return []



    @staticmethod
    async def _search_authors(
        session: AsyncSession,
        query: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[AuthorSearchResult]:
        """
        Search for authors based on their posts.
        Aggregates author statistics from posts table.
        """
        try:
            author_query = text("""
                SELECT 
                    author_id::text,
                    COUNT(DISTINCT id)::integer as posts_count,
                    COALESCE(SUM(total_likes), 0)::integer as total_likes
                FROM posts
                WHERE author_id::text ILIKE :like_query
                GROUP BY author_id
                ORDER BY total_likes DESC, posts_count DESC
                OFFSET :skip LIMIT :limit
            """)
            
            result = await session.exec(author_query, {  # type: ignore
                "like_query": f"%{query}%",
                "skip": skip,
                "limit": limit
            })
            rows = result.all()
            
            authors = [
                AuthorSearchResult(
                    id=row[0],
                    name=f"User {row[0][:8]}",
                    posts_count=row[1],
                    total_likes=row[2]
                )
                for row in rows
            ]
            
            logger.info(f"Found {len(authors)} authors matching query '{query}'")
            return authors
            
        except Exception as e:
            logger.error(f"Error in _search_authors: {str(e)}", exc_info=True)
            return []



    @staticmethod
    async def _search_recipes(
        query: str,
        tags: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 20,
        auth_token: Optional[str] = None
    ) -> List[RecipeSearchResult]:
        """
        Search recipes from Recipe Service (MongoDB).
        Makes HTTP call to recipe-service search endpoint.
        """
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                headers = {}
                if auth_token:
                    headers["Authorization"] = auth_token
                
                params = {
                    "skip": skip,
                    "limit": limit * 2  
                }
                
                response = await client.get(
                    f"{SearchService.RECIPE_SERVICE_URL}/recipes",
                    params=params,
                    headers=headers
                )
                
                if response.status_code == 200:
                    recipes_data = response.json()
                    recipes = []
                    
                    for recipe in recipes_data:
                        # Filtruj lokalnie po nazwie/opisie
                        name = recipe.get("name", "").lower()
                        description = recipe.get("description", "").lower()
                        search_lower = query.lower()
                        
                        if search_lower not in name and search_lower not in description:
                            continue
                        
                        # Filter by tags if specified
                        recipe_tags = recipe.get("tags", [])
                        if tags and not any(t in recipe_tags for t in tags):
                            continue
                            
                        recipes.append(RecipeSearchResult(
                            id=str(recipe.get("_id", "")),
                            name=recipe.get("name", ""),
                            description=recipe.get("description", ""),
                            author_id=str(recipe.get("author_id", "")) if recipe.get("author_id") else None,
                            prep_time=recipe.get("prep_time"),
                            difficulty=recipe.get("difficulty"),
                            tags=recipe_tags,
                            image_url=recipe.get("image_url")
                        ))
                        

                        if len(recipes) >= limit:
                            break
                    
                    logger.info(f"Found {len(recipes)} recipes matching query '{query}'")
                    return recipes
                else:
                    logger.warning(f"Recipe service returned status {response.status_code}")
                    return []
                    
        except httpx.TimeoutException:
            logger.warning("Recipe service request timed out")
            return []
        except Exception as e:
            logger.error(f"Error searching recipes: {str(e)}")
            return []



    @staticmethod
    async def _search_workouts(
        query: str,
        tags: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 20,
        auth_token: Optional[str] = None
    ) -> List[WorkoutSearchResult]:
        """
        Search workouts from Workout Service (MongoDB).
        Makes HTTP call to workout-service search endpoint.
        """
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                headers = {}
                if auth_token:
                    headers["Authorization"] = auth_token
                
                params = {
                    "skip": skip,
                    "limit": limit * 2
                }
                
                response = await client.get(
                    f"{SearchService.WORKOUT_SERVICE_URL}/workouts/exercises",
                    params=params,
                    headers=headers
                )
                
                if response.status_code == 200:
                    workouts_data = response.json()
                    workouts = []
                    
                    for workout in workouts_data:
                        # Filtruje lokalnie po nazwie/opisie
                        name = workout.get("name", "").lower()
                        description = workout.get("description", "").lower()
                        search_lower = query.lower()
                        
                        if search_lower not in name and search_lower not in description:
                            continue
                        
                        workout_tags = workout.get("tags", [])
                        if tags and not any(t in workout_tags for t in tags):
                            continue
                        
                        workouts.append(WorkoutSearchResult(
                            id=str(workout.get("_id", "")),
                            name=workout.get("name", ""),
                            description=workout.get("description", ""),
                            author_id=None,
                            duration=None,
                            difficulty=workout.get("advancement"),
                            workout_type=workout.get("category"),
                            tags=workout_tags,
                            image_url=None
                        ))
                        
                        # Ogranicz do limitu
                        if len(workouts) >= limit:
                            break
                    
                    logger.info(f"Found {len(workouts)} workouts matching query '{query}'")
                    return workouts
                else:
                    logger.warning(f"Workout service returned status {response.status_code}")
                    return []
                    
        except httpx.TimeoutException:
            logger.warning("Workout service request timed out")
            return []
        except Exception as e:
            logger.error(f"Error searching workouts: {str(e)}")
            return []



    @staticmethod
    async def get_search_suggestions(
        session: AsyncSession,
        query: str,
        limit: int = 10
    ) -> SearchSuggestionsResponse:
        """
        Get autocomplete suggestions based on partial query.
        Returns matching post titles and popular tags.
        """
        try:
            suggestions: List[str] = []
            
            if len(query) >= 2:

                title_query = text("""
                    SELECT DISTINCT title
                    FROM posts
                    WHERE title ILIKE :like_query
                    ORDER BY total_likes DESC
                    LIMIT :limit
                """)
                
                result = await session.exec(title_query, {  # type: ignore
                    "like_query": f"%{query}%",
                    "limit": limit
                })
                suggestions = [row[0] for row in result.all()]
            
            # Get matching tags
            tags = await SearchService.get_popular_tags(
                session=session,
                query=query,
                limit=5
            )
            
            return SearchSuggestionsResponse(
                query=query,
                suggestions=suggestions,
                tags=tags
            )
            
        except Exception as e:
            logger.error(f"Error getting search suggestions: {str(e)}", exc_info=True)
            return SearchSuggestionsResponse(query=query)
    
    @staticmethod
    async def get_popular_tags(
        session: AsyncSession,
        query: Optional[str] = None,
        limit: int = 20
    ) -> List[TagSuggestion]:
        """
        Get popular tags from posts, optionally filtered by query.
        """
        try:
            if query:

                tag_query = text("""
                    SELECT tag, COUNT(*)::integer as count
                    FROM posts, unnest(tags) AS tag
                    WHERE tag ILIKE :like_query
                    GROUP BY tag
                    ORDER BY count DESC
                    LIMIT :limit
                """)
                params: dict = {"like_query": f"%{query}%", "limit": limit}
            else:

                tag_query = text("""
                    SELECT tag, COUNT(*)::integer as count
                    FROM posts, unnest(tags) AS tag
                    GROUP BY tag
                    ORDER BY count DESC
                    LIMIT :limit
                """)
                params = {"limit": limit}
            
            result = await session.exec(tag_query, params)  # type: ignore
            rows = result.all()
            
            return [
                TagSuggestion(tag=row[0], count=row[1])
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Error getting popular tags: {str(e)}", exc_info=True)
            return []
    
    
    @staticmethod
    async def search_by_tag(
        session: AsyncSession,
        tag: str,
        sort_by: SearchSortBy = SearchSortBy.NEWEST,
        skip: int = 0,
        limit: int = 20
    ) -> List[PostSearchResult]:
        """
        Search posts by specific tag.
        """
        try:
            sort_clause = {
                SearchSortBy.RELEVANCE: "created_at DESC",
                SearchSortBy.NEWEST: "created_at DESC",
                SearchSortBy.TRENDING: "trending_coefficient DESC, created_at DESC",
                SearchSortBy.MOST_LIKED: "total_likes DESC, created_at DESC"
            }.get(sort_by, "created_at DESC")
            
            # ZMIENIONE: Uproszczone
            tag_query = text(f"""
                SELECT 
                    id::text,
                    title,
                    content,
                    author_id::text,
                    tags,
                    images,
                    total_likes,
                    views_count,
                    trending_coefficient,
                    created_at,
                    updated_at
                FROM posts
                WHERE :tag = ANY(tags)
                ORDER BY {sort_clause}
                OFFSET :skip LIMIT :limit
            """)
            
            result = await session.exec(tag_query, {  # type: ignore
                "tag": tag,
                "skip": skip,
                "limit": limit
            })
            rows = result.all()
            
            posts = []
            for row in rows:
                comment_count_query = text("""
                    SELECT COUNT(*)::integer 
                    FROM comments 
                    WHERE post_id = CAST(:post_id AS uuid)
                """)
                comment_count_result = await session.exec(
                    comment_count_query, 
                    {"post_id": row[0]}
                )  # type: ignore
                comments_count = comment_count_result.scalar() or 0
                
                posts.append(PostSearchResult(
                    id=row[0],
                    title=row[1],
                    content=(row[2][:500] if row[2] else ""),
                    author_id=row[3],
                    tags=row[4] or [],
                    images=row[5] or [],
                    total_likes=row[6] or 0,
                    views_count=row[7] or 0,
                    comments_count=comments_count,
                    trending_coefficient=float(row[8] or 0),
                    created_at=row[9],
                    updated_at=row[10],
                    relevance_score=1.0
                ))
            
            logger.info(f"Found {len(posts)} posts with tag '{tag}'")
            return posts
            
        except Exception as e:
            logger.error(f"Error in search_by_tag: {str(e)}", exc_info=True)
            return []