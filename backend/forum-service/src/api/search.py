from fastapi import APIRouter, Depends, Query, Header, status, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Dict, Optional
import logging
from src.db.main import get_session
from src.services.search_service import SearchService
from src.validators.search import (
    SearchQuery, SearchCategory, SearchSortBy,
    SearchResponse, SearchSuggestionsResponse,
    PostSearchResult, TagSuggestion
)
from common.auth_guard import require_auth


logger = logging.getLogger(__name__)


router = APIRouter()


def get_authorization_header(
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> Optional[str]:
    """Extract Authorization header for forwarding to external services"""
    return authorization



# ============ MAIN SEARCH ENDPOINT ============
@router.get("/search", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def search(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    category: SearchCategory = Query(default=SearchCategory.ALL, description="Category filter"),
    tags: Optional[List[str]] = Query(default=None, description="Filter by tags"),
    author_id: Optional[str] = Query(default=None, description="Filter by author ID"),
    sort_by: SearchSortBy = Query(default=SearchSortBy.RELEVANCE, description="Sort order"),
    skip: int = Query(default=0, ge=0, description="Pagination offset"),
    limit: int = Query(default=20, ge=1, le=100, description="Results per page"),
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth),
    auth_header: Optional[str] = Depends(get_authorization_header)
):
    """
    Perform full-text search across forum content.
    
    Supports searching in:
    - **all**: All categories combined
    - **posts**: Forum posts only
    - **recipes**: Recipes from recipe service
    - **workouts**: Workouts from workout service
    - **authors**: Post authors
    
    Results can be sorted by:
    - **relevance**: Best matching results first
    - **newest**: Most recent first
    - **trending**: Highest trending coefficient first
    - **most_liked**: Most liked first
    """
    try:
        search_query = SearchQuery(
            query=q,
            category=category,
            tags=tags,
            author_id=author_id,
            sort_by=sort_by,
            skip=skip,
            limit=limit
        )
        
        return await SearchService.search(
            session=session,
            search_query=search_query,
            auth_token=auth_header
        )
    except ValueError as e:
        logger.error(f"Validation error in search: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error performing search: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to perform search")



@router.post("/search", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def search_post(
    search_query: SearchQuery,
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth),
    auth_header: Optional[str] = Depends(get_authorization_header)
):
    """
    Perform full-text search with request body.
    Alternative to GET /search for complex queries.
    """
    try:
        return await SearchService.search(
            session=session,
            search_query=search_query,
            auth_token=auth_header
        )
    except ValueError as e:
        logger.error(f"Validation error in search_post: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error performing search_post: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to perform search")



# ============ AUTOCOMPLETE / SUGGESTIONS ============
@router.get("/search/suggestions", response_model=SearchSuggestionsResponse, status_code=status.HTTP_200_OK)
async def get_search_suggestions(
    q: str = Query(..., min_length=2, max_length=100, description="Partial search query"),
    limit: int = Query(default=10, ge=1, le=20, description="Maximum suggestions"),
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth)
):
    """
    Get search autocomplete suggestions.
    Returns matching post titles and popular tags.
    """
    try:
        return await SearchService.get_search_suggestions(
            session=session,
            query=q,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error getting search suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get suggestions")



# ============ TAG-BASED SEARCH ============
@router.get("/search/tags", response_model=List[TagSuggestion], status_code=status.HTTP_200_OK)
async def get_popular_tags(
    q: Optional[str] = Query(default=None, max_length=50, description="Filter tags by query"),
    limit: int = Query(default=20, ge=1, le=50, description="Maximum tags to return"),
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth)
):
    """
    Get popular tags from forum posts.
    Optionally filter by partial tag name.
    """
    try:
        return await SearchService.get_popular_tags(
            session=session,
            query=q,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error getting popular tags: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get popular tags")



@router.get("/search/by-tag/{tag}", response_model=List[PostSearchResult], status_code=status.HTTP_200_OK)
async def search_by_tag(
    tag: str,
    sort_by: SearchSortBy = Query(default=SearchSortBy.NEWEST, description="Sort order"),
    skip: int = Query(default=0, ge=0, description="Pagination offset"),
    limit: int = Query(default=20, ge=1, le=100, description="Results per page"),
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth)
):
    """
    Get all posts with a specific tag.
    """
    try:
        if not tag or len(tag.strip()) == 0:
            raise HTTPException(status_code=400, detail="Tag cannot be empty")
        
        return await SearchService.search_by_tag(
            session=session,
            tag=tag,
            sort_by=sort_by,
            skip=skip,
            limit=limit
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching by tag: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search by tag")



# ============ CATEGORY-SPECIFIC SEARCH ============
@router.get("/search/posts", response_model=List[PostSearchResult], status_code=status.HTTP_200_OK)
async def search_posts_only(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    tags: Optional[List[str]] = Query(default=None, description="Filter by tags"),
    author_id: Optional[str] = Query(default=None, description="Filter by author ID"),
    sort_by: SearchSortBy = Query(default=SearchSortBy.RELEVANCE, description="Sort order"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth)
):
    """
    Search only in forum posts.
    Faster than general search when you only need posts.
    """
    try:
        return await SearchService._search_posts(
            session=session,
            query=q,
            tags=tags,
            author_id=author_id,
            sort_by=sort_by,
            skip=skip,
            limit=limit
        )
    except ValueError as e:
        logger.error(f"Validation error searching posts: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error searching posts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search posts")
