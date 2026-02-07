import sqlalchemy.dialects.postgresql as pg
from sqlmodel import SQLModel, Field, Relationship, Column
from datetime import datetime, timezone
from typing import Optional, List
import uuid


class Post(SQLModel, table=True):
    """Model for forum posts"""

    __tablename__ = "posts"

    id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            nullable=False,
            primary_key=True,
            default=uuid.uuid4
        )
    )
    
    author_id: uuid.UUID = Field(
        description="User ID of the post author"
    )
    
    title: str = Field(
        min_length=3,
        max_length=200,
        description="Title of the post."
    )
    
    content: str = Field(
        min_length=3,
        max_length=500,
        description="Content of the post."
    )
    
    comments: Optional[List["Comment"]] = Relationship(
        back_populates="post"
    )
    
    total_likes: int = Field(
        default=0,
        ge=0,
        description="Number of likes on the post"
    )
    
    images: Optional[List[str]] = Field(
        sa_column=Column(pg.ARRAY(pg.TEXT)),
        default=None,
        description="List of image URLs"
    )

    views_count: int = Field(
        default=0,
        ge=0,
        description="Number of views on the post"
    )

    tags: Optional[List[str]] = Field(
        sa_column=Column(pg.ARRAY(pg.TEXT)),
        default=None,
        description="Tags associated with the post"
    )

    linked_recipes: Optional[List[str]] = Field(
        sa_column=Column(pg.ARRAY(pg.TEXT)),
        default=None,
        description="List of recipe IDs linked to this post"
    )

    linked_workouts: Optional[List[str]] = Field(
        sa_column=Column(pg.ARRAY(pg.TEXT)),
        default=None,
        description="List of workout/exercise IDs linked to this post"
    )

    trending_coefficient: float = Field(
        default=0.0,
        description="Coefficient to determine the trending status of the post"
    )

    created_at: datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            nullable=False,
            default=lambda: datetime.now(timezone.utc)
        ),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    
    updated_at: datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            nullable=False,
            default=lambda: datetime.now(timezone.utc),
            onupdate=lambda: datetime.now(timezone.utc)
        ),
        default_factory=lambda: datetime.now(timezone.utc)
    )