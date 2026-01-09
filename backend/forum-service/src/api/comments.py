from fastapi import APIRouter, Depends, status, HTTPException, Query, Header
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Dict, Optional
from uuid import UUID

from src.db.main import get_session
from src.services.comment_service import CommentService
from src.services.like_service import LikeService
from src.validators.comment import CommentCreate, CommentUpdate, CommentResponse
from src.validators.nested import CommentTreeResponse

from common.auth_guard import require_auth

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



@router.post("/posts/{post_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: UUID,
    comment_data: CommentCreate,
    session: AsyncSession = Depends(get_session),
    author_id: str = Depends(get_required_user_id),
    token_payload: Dict = Depends(require_auth)
):
    """Create a new comment on a post"""
    try:
        user_uuid = UUID(str(author_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid User ID format. Expected UUID, got: {author_id}"
        )
    
    if comment_data.parent_comment_id:
        try:
            parent_id = UUID(comment_data.parent_comment_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid parent_comment_id format. Expected UUID, got: {comment_data.parent_comment_id}"
            )
    else:
        parent_id = None
    
    comment = await CommentService.create_comment(
        session=session,
        post_id=post_id,
        author_id=user_uuid,
        content=comment_data.content,
        parent_comment_id=parent_id
    )
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post or parent comment not found"
        )
    
    return CommentResponse(
        id=str(comment.id),
        post_id=str(comment.post_id),
        user_id=str(comment.author_id),
        content=comment.content,
        parent_comment_id=str(comment.parent_comment_id) if comment.parent_comment_id else None,
        total_likes=comment.total_likes,
        created_at=comment.created_at,
        updated_at=comment.updated_at
    )



@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse], status_code=status.HTTP_200_OK)
async def get_comments_by_post(
    post_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth)
):
    """Get top-level comments for a post"""
    comments = await CommentService.get_comments_by_post(
        session=session,
        post_id=post_id,
        skip=skip,
        limit=limit
    )
    
    return [
        CommentResponse(
            id=str(comment.id),
            post_id=str(comment.post_id),
            user_id=str(comment.author_id),
            content=comment.content,
            parent_comment_id=str(comment.parent_comment_id) if comment.parent_comment_id else None,
            total_likes=comment.total_likes,
            created_at=comment.created_at,
            updated_at=comment.updated_at
        )
        for comment in comments
    ]



@router.get("/posts/{post_id}/comments/tree", response_model=List[CommentTreeResponse], status_code=status.HTTP_200_OK)
async def get_comments_tree(
    post_id: UUID,
    max_depth: int = Query(3, ge=1, le=10),
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth)
):
    """Get comments with nested replies in tree structure"""
    tree = await CommentService.get_comments_tree(
        session=session,
        post_id=post_id,
        max_depth=max_depth
    )
    
    def format_tree_node(node: dict) -> CommentTreeResponse:
        comment = node["comment"]
        return CommentTreeResponse(
            comment=CommentResponse(
                id=str(comment.id),
                post_id=str(comment.post_id),
                user_id=str(comment.author_id),
                content=comment.content,
                parent_comment_id=str(comment.parent_comment_id) if comment.parent_comment_id else None,
                total_likes=comment.total_likes,
                created_at=comment.created_at,
                updated_at=comment.updated_at
            ),
            replies=[format_tree_node(reply) for reply in node["replies"]]
        )
    
    return [format_tree_node(node) for node in tree]



@router.get("/comments/{comment_id}", response_model=CommentResponse, status_code=status.HTTP_200_OK)
async def get_comment(
    comment_id: UUID,
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth)
):
    """Get a single comment by ID"""
    comment = await CommentService.get_comment_by_id(
        session=session,
        comment_id=comment_id
    )
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comment {comment_id} not found"
        )
    
    return CommentResponse(
        id=str(comment.id),
        post_id=str(comment.post_id),
        user_id=str(comment.author_id),
        content=comment.content,
        parent_comment_id=str(comment.parent_comment_id) if comment.parent_comment_id else None,
        total_likes=comment.total_likes,
        created_at=comment.created_at,
        updated_at=comment.updated_at
    )



@router.get("/comments/{comment_id}/replies", response_model=List[CommentResponse], status_code=status.HTTP_200_OK)
async def get_comment_replies(
    comment_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth)
):
    """Get direct replies to a comment"""
    replies = await CommentService.get_comment_replies(
        session=session,
        parent_comment_id=comment_id,
        skip=skip,
        limit=limit
    )
    
    return [
        CommentResponse(
            id=str(reply.id),
            post_id=str(reply.post_id),
            user_id=str(reply.author_id),
            content=reply.content,
            parent_comment_id=str(reply.parent_comment_id) if reply.parent_comment_id else None,
            total_likes=reply.total_likes,
            created_at=reply.created_at,
            updated_at=reply.updated_at
        )
        for reply in replies
    ]



@router.patch("/comments/{comment_id}", response_model=CommentResponse, status_code=status.HTTP_200_OK)
async def update_comment(
    comment_id: UUID,
    comment_data: CommentUpdate,
    session: AsyncSession = Depends(get_session),
    author_id: str = Depends(get_required_user_id),
    token_payload: Dict = Depends(require_auth)
):
    """Update a comment"""
    try:
        user_uuid = UUID(str(author_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid User ID format. Expected UUID, got: {author_id}"
        )
    
    comment = await CommentService.update_comment(
        session=session,
        comment_id=comment_id,
        author_id=user_uuid,
        content=comment_data.content
    )
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found or user is not the author"
        )
    
    return CommentResponse(
        id=str(comment.id),
        post_id=str(comment.post_id),
        user_id=str(comment.author_id),
        content=comment.content,
        parent_comment_id=str(comment.parent_comment_id) if comment.parent_comment_id else None,
        total_likes=comment.total_likes,
        created_at=comment.created_at,
        updated_at=comment.updated_at
    )



@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: UUID,
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth),
    x_user_id: str = Header(None, alias="X-User-Id"),
):
    """Delete a comment and all its replies"""
    author_id = get_user_id_from_header(x_user_id)
    
    if not author_id:
        author_id = token_payload.get("internal_uid")
    
    try:
        user_uuid = UUID(str(author_id))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid User ID format. Expected UUID, got: {author_id}"
        )
    
    success = await CommentService.delete_comment(
        session=session,
        comment_id=comment_id,
        author_id=user_uuid
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found or user is not the author"
        )



@router.post("/comments/{comment_id}/like", response_model=dict, status_code=status.HTTP_200_OK)
async def like_comment(
    comment_id: UUID,
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_required_user_id),
    token_payload: Dict = Depends(require_auth)
):
    """Like a comment"""
    try:
        user_uuid = UUID(str(user_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid User ID format. Expected UUID, got: {user_id}"
        )
    
    success = await LikeService.track_comment_like(
        session=session,
        comment_id=comment_id,
        user_id=user_uuid
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment not found or already liked"
        )
    
    return {"message": "Comment liked successfully"}



@router.delete("/comments/{comment_id}/like", response_model=dict, status_code=status.HTTP_200_OK)
async def unlike_comment(
    comment_id: UUID,
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_required_user_id),
    token_payload: Dict = Depends(require_auth)
):
    """Remove like from a comment"""
    try:
        user_uuid = UUID(str(user_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid User ID format. Expected UUID, got: {user_id}"
        )
    
    success = await LikeService.remove_comment_like(
        session=session,
        comment_id=comment_id,
        user_id=user_uuid
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment not found or not liked"
        )
    
    return {"message": "Comment unliked successfully"}



@router.get("/comments/{comment_id}/likes", response_model=dict, status_code=status.HTTP_200_OK)
async def get_comment_likes_count(
    comment_id: UUID,
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth)
):
    """Get like count for a comment"""
    count = await LikeService.get_comment_likes_count(
        session=session,
        comment_id=comment_id
    )
    
    if count is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    return {"comment_id": str(comment_id), "likes_count": count}