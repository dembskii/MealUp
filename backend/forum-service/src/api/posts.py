from fastapi import APIRouter, HTTPException, Depends, Query, Header, status
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional, List, Dict
from uuid import UUID
import logging

from src.services.post_service import PostService
from src.validators.post import PostCreate, PostUpdate, PostResponse
from src.db.main import get_session

from common.auth_guard import require_auth


logger = logging.getLogger(__name__)
router = APIRouter()


def get_user_id_from_header(x_user_id: Optional[str] = Header(None, alias="X-User-Id")) -> Optional[str]:
    """Extract user ID from header (set by gateway after auth) - returns None if not present"""
    return x_user_id


def get_required_user_id(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    token_payload: Dict = Depends(require_auth)
) -> str:
    """Get user ID from header or token payload - raises 401 if neither available"""
    if x_user_id:
        return x_user_id
    
    user_id = token_payload.get("internal_uid") or token_payload.get("sub")
    if user_id:
        return user_id
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User ID not found in header or token"
    )


@router.get("/posts", response_model=List[PostResponse], status_code=status.HTTP_200_OK)
async def get_all_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session)
):
    """Get all posts with pagination"""
    posts = await PostService.get_all_posts(session, skip, limit)
    return posts


@router.get("/posts/trending", response_model=List[PostResponse], status_code=status.HTTP_200_OK)
async def get_trending_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    min_coefficient: float = Query(0.0, ge=0.0),
    session: AsyncSession = Depends(get_session)
):
    """Get trending posts sorted by trending coefficient"""
    posts = await PostService.get_trending_posts(session, skip, limit, min_coefficient)
    return posts


@router.get("/posts/{post_id}", response_model=PostResponse, status_code=status.HTTP_200_OK)
async def get_post_by_id(
    post_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """Get a specific post by ID"""
    post = await PostService.get_post_by_id(session, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


@router.post("/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    session: AsyncSession = Depends(get_session),
    author_id: str = Depends(get_required_user_id),
):
    """Create a new post"""
    # Konwersja na UUID (wymagane przez bazę danych)
    try:
        uuid_author_id = UUID(str(author_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Invalid User ID format. Expected UUID, got: {author_id}"
        )
    
    post_dict = post_data.model_dump()
    post_dict["author_id"] = uuid_author_id
    
    post = await PostService.create_post(session, post_dict)
    if not post:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create post")
    
    return post



@router.put("/posts/{post_id}", response_model=PostResponse, status_code=status.HTTP_200_OK)
async def update_post(
    post_id: UUID,
    post_data: PostUpdate,
    session: AsyncSession = Depends(get_session),
    author_id: str = Depends(get_required_user_id),
):
    """Update an existing post"""
    existing_post = await PostService.get_post_by_id(session, post_id)
    if not existing_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    if str(existing_post.author_id) != str(author_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this post")
    
    post_dict = post_data.model_dump(exclude_unset=True)
    updated_post = await PostService.update_post(session, post_id, post_dict)
    
    if not updated_post:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update post")
    
    return updated_post



@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: UUID,
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth),
    x_user_id: str = Header(None, alias="X-User-Id"),
):
    """Delete a post"""
    existing_post = await PostService.get_post_by_id(session, post_id)
    if not existing_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    author_id = author_id = get_user_id_from_header(x_user_id)
    
    if not author_id:
        author_id = token_payload.get("internal_uid")

    if not author_id or str(existing_post.author_id) != str(author_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this post")
    
    success = await PostService.delete_post(session, post_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete post")



# ============ VIEW TRACKING ============
@router.post("/posts/{post_id}/view", status_code=status.HTTP_200_OK)
async def track_post_view(
    post_id: UUID,
    engagement_seconds: Optional[int] = Query(None, ge=0),
    session: AsyncSession = Depends(get_session),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    """Track a view on a post (user_id optional for anonymous views)"""
    user_uuid = None
    if x_user_id:
        try:
            user_uuid = UUID(x_user_id)
        except ValueError:
            pass
    
    success = await PostService.track_post_view(
        session,
        post_id,
        user_uuid,
        engagement_seconds
    )
    
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    return {"message": "View tracked successfully"}



@router.get("/posts/{post_id}/views", response_model=dict, status_code=status.HTTP_200_OK)
async def get_post_views(
    post_id: UUID,
    hours: Optional[int] = Query(None, ge=1),
    session: AsyncSession = Depends(get_session)
):
    """Get view count for a post"""
    count = await PostService.get_post_views_count(session, post_id, hours)
    
    return {
        "post_id": str(post_id),
        "views_count": count,
        "timeframe_hours": hours
    }


# ============ TRENDING COEFFICIENT ============
@router.post("/posts/{post_id}/calculate-trending", response_model=dict, status_code=status.HTTP_200_OK)
async def calculate_trending_coefficient(
    post_id: UUID,
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth)
):
    """Calculate trending coefficient for a specific post"""
    coefficient = await PostService.calculate_trending_coefficient(session, post_id)
    
    if coefficient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    return {
        "post_id": str(post_id),
        "trending_coefficient": coefficient
    }



@router.post("/posts/recalculate-trending", response_model=dict, status_code=status.HTTP_200_OK)
async def recalculate_all_trending(
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth)
):
    """Recalculate trending coefficients for all posts (admin/background task)"""
    updated_count = await PostService.recalculate_all_trending_coefficients(session)
    
    return {
        "message": "Trending coefficients recalculated",
        "updated_posts": updated_count
    }