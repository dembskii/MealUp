import sqlalchemy.dialects.postgresql as pg
from sqlmodel import SQLModel, Field, Column
from datetime import datetime
import uuid


class PostLike(SQLModel, table=True):
    """Tracks which users liked which posts"""
    __tablename__ = "post_likes"

    id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            nullable=False,
            primary_key=True,
            default=uuid.uuid4
        )
    )

    user_id: uuid.UUID = Field(
        description="User ID who liked the post"
    )

    post_uid: uuid.UUID = Field(
        foreign_key="posts.uid",
        description="Reference to the liked post"
    )

    created_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP, default=datetime.now),
        default_factory=datetime.now
    )

    class Config:
        unique_together = [("user_id", "post_uid")]