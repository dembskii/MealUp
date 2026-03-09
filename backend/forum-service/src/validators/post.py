from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from uuid import UUID



class PostCreate(BaseModel):
    """Schema for creating a new post"""
    title: str = Field(
        ...,
        min_length=3,
        max_length=200,
        examples=["Best Recipe for Muscle Gain"],
        description="Title of the post"
    )
    content: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        examples=["Here's my favorite recipe for post-workout meal..."],
        description="Content of the post"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        max_length=10,
        examples=[["recipe", "fitness", "nutrition"]],
        description="List of tags associated with the post"
    )
    images: Optional[List[str]] = Field(
        default=None,
        max_length=5,
        examples=[["https://example.com/image1.jpg"]],
        description="List of image URLs"
    )
    linked_recipes: Optional[List[str]] = Field(
        default=None,
        examples=[["550e8400-e29b-41d4-a716-446655440001"]],
        description="List of recipe IDs to link to the post"
    )
    linked_workouts: Optional[List[str]] = Field(
        default=None,
        examples=[["550e8400-e29b-41d4-a716-446655440002"]],
        description="List of workout/exercise IDs to link to the post"
    )


class PostUpdate(BaseModel):
    """Schema for updating an existing post"""
    title: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=200,
        examples=["Updated Post Title"],
        description="Updated title of the post"
    )
    content: Optional[str] = Field(
        default=None,
        min_length=10,
        max_length=5000,
        examples=["Updated content..."],
        description="Updated content of the post"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        max_length=10,
        examples=[["recipe", "fitness"]],
        description="Updated list of tags"
    )
    images: Optional[List[str]] = Field(
        None,
        max_length=5,
        examples=[["https://example.com/new-image.jpg"]],
        description="Updated list of image URLs"
    )
    linked_recipes: Optional[List[str]] = Field(
        default=None,
        description="Updated list of linked recipe IDs"
    )
    linked_workouts: Optional[List[str]] = Field(
        default=None,
        description="Updated list of linked workout/exercise IDs"
    )


class PostResponse(BaseModel):
    """Schema for post response"""
    id: UUID = Field(
        alias="_id",
        description="Unique post ID"
    )
    author_id: UUID = Field(
        description="ID of the user who created the post"
    )
    title: str = Field(
        examples=["Best Recipe for Muscle Gain"],
        description="Title of the post"
    )
    content: str = Field(
        examples=["Here's my favorite recipe..."],
        description="Content of the post"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        examples=[["recipe", "fitness"]],
        description="List of tags associated with the post"
    )
    images: Optional[List[str]] = Field(
        default=None,
        examples=[["https://example.com/image.jpg"]],
        description="List of image URLs"
    )
    linked_recipes: Optional[List[str]] = Field(
        default=None,
        description="List of linked recipe IDs"
    )
    linked_workouts: Optional[List[str]] = Field(
        default=None,
        description="List of linked workout/exercise IDs"
    )
    total_likes: int = Field(
        ge=0,
        examples=[42],
        description="Total number of likes on the post"
    )
    views_count: int = Field(
        ge=0,
        examples=[156],
        description="Total number of views on the post"
    )
    created_at: datetime = Field(
        alias="_created_at",
        description="Timestamp when the post was created"
    )
    updated_at: datetime = Field(
        alias="_updated_at",
        description="Timestamp when the post was last updated"
    )

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "auth0|1234567890",
                "title": "Best Recipe for Muscle Gain",
                "content": "Here's my favorite recipe for post-workout meal...",
                "tags": ["recipe", "fitness", "nutrition"],
                "images": ["https://example.com/image1.jpg"],
                "total_likes": 42,
                "total_views": 156,
                "total_comments": 23,
                "_created_at": "2024-01-15T10:30:00",
                "_updated_at": "2024-01-15T10:30:00"
            }
        }
    )
