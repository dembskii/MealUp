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