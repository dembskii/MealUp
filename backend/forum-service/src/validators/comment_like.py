from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime



class CommentLikeCreate(BaseModel):
    """Schema for creating a comment like"""
    pass


class CommentLikeResponse(BaseModel):
    """Schema for comment like response"""
    id: str = Field(
        alias="_id",
        description="Unique like ID"
    )
    comment_id: str = Field(
        description="ID of the liked comment"
    )
    user_id: str = Field(
        description="ID of the user who liked the comment"
    )
    created_at: datetime = Field(
        alias="_created_at",
        description="Timestamp when the like was created"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "550e8400-e29b-41d4-a716-446655440004",
                "comment_id": "550e8400-e29b-41d4-a716-446655440002",
                "user_id": "auth0|1234567890",
                "_created_at": "2024-01-15T10:45:00"
            }
        }
    )
