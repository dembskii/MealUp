from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime



class PostViewCreate(BaseModel):
    """Schema for creating a post view"""
    pass


class PostViewResponse(BaseModel):
    """Schema for post view response"""
    id: str = Field(
        alias="_id",
        description="Unique view ID"
    )
    post_id: str = Field(
        description="ID of the viewed post"
    )
    user_id: str = Field(
        description="ID of the user who viewed the post"
    )
    created_at: datetime = Field(
        alias="_created_at",
        description="Timestamp when the view was recorded"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "550e8400-e29b-41d4-a716-446655440005",
                "post_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "auth0|1234567890",
                "_created_at": "2024-01-15T10:50:00"
            }
        }
    )