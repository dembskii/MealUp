from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional




class CommentCreate(BaseModel):
    """Schema for creating a new comment"""
    content: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        examples=["Great post! Thanks for sharing this recipe."],
        description="Content of the comment"
    )
    parent_comment_id: Optional[str] = Field(
        default=None,
        examples=["550e8400-e29b-41d4-a716-446655440001"],
        description="ID of parent comment if this is a reply"
    )


class CommentUpdate(BaseModel):
    """Schema for updating an existing comment"""
    content: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        examples=["Updated comment content..."],
        description="Updated content of the comment"
    )


class CommentResponse(BaseModel):
    """Schema for comment response"""
    id: str = Field(
        alias="_id",
        description="Unique comment ID"
    )
    post_id: str = Field(
        description="ID of the post this comment belongs to"
    )
    user_id: str = Field(
        description="ID of the user who created the comment"
    )
    content: str = Field(
        examples=["Great post!"],
        description="Content of the comment"
    )
    parent_comment_id: Optional[str] = Field(
        default=None,
        examples=["550e8400-e29b-41d4-a716-446655440001"],
        description="ID of parent comment if this is a reply"
    )
    total_likes: int = Field(
        ge=0,
        examples=[15],
        description="Total number of likes on the comment"
    )
    created_at: datetime = Field(
        alias="_created_at",
        description="Timestamp when the comment was created"
    )
    updated_at: datetime = Field(
        alias="_updated_at",
        description="Timestamp when the comment was last updated"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "550e8400-e29b-41d4-a716-446655440002",
                "post_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "auth0|1234567890",
                "content": "Great post! Thanks for sharing.",
                "parent_comment_id": None,
                "total_likes": 15,
                "_created_at": "2024-01-15T10:35:00",
                "_updated_at": "2024-01-15T10:35:00"
            }
        }
    )
