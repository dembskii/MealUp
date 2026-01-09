from pydantic import BaseModel, Field, ConfigDict
from typing import List
from .post import PostResponse
from .comment import CommentResponse


class PostListResponse(BaseModel):
    """Schema for list of posts"""
    total: int = Field(
        ge=0,
        description="Total number of posts matching the query"
    )
    items: List[PostResponse] = Field(
        description="List of posts"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 42,
                "items": []
            }
        }
    )


class CommentListResponse(BaseModel):
    """Schema for list of comments"""
    total: int = Field(
        ge=0,
        description="Total number of comments for the post"
    )
    items: List[CommentResponse] = Field(
        description="List of comments"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 23,
                "items": []
            }
        }
    )


class CommentTreeResponse(BaseModel):
    """Schema for nested comment tree structure"""
    comment: CommentResponse = Field(
        description="The comment data"
    )
    replies: List["CommentTreeResponse"] = Field(
        default=[],
        description="Nested replies to this comment"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "comment": {
                    "_id": "550e8400-e29b-41d4-a716-446655440002",
                    "post_id": "550e8400-e29b-41d4-a716-446655440000",
                    "user_id": "auth0|1234567890",
                    "content": "Great post!",
                    "parent_comment_id": None,
                    "total_likes": 15,
                    "_created_at": "2024-01-15T10:35:00",
                    "_updated_at": "2024-01-15T10:35:00"
                },
                "replies": []
            }
        }
    )