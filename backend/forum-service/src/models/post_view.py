import sqlalchemy.dialects.postgresql as pg
from sqlmodel import SQLModel, Field, Column
from datetime import datetime
from typing import Optional
import uuid


class PostView(SQLModel, table=True):
    """Tracks post views for trending calculation"""
    __tablename__ = "post_views"

    id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            nullable=False,
            primary_key=True,
            default=uuid.uuid4
        )
    )

    user_id: Optional[uuid.UUID] = Field(
        default=None,
        description="User ID who viewed the post (nullable for anonymous views)"
    )

    post_id: uuid.UUID = Field(
        foreign_key="posts.id",
        description="Reference to the viewed post"
    )

    viewed_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP, default=datetime.now),
        default_factory=datetime.now,
        description="Timestamp of the view"
    )

    engagement_seconds: Optional[int] = Field(
        default=None,
        description="How long user spent viewing the post in seconds"
    )