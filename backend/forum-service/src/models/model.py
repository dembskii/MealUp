import sqlalchemy.dialects.postgresql as pg
from sqlmodel import SQLModel, Field, Relationship, Column
from datetime import datetime
from typing import Optional, List
import uuid




class Comment(SQLModel, table=True):
    __tablename__ = "comments"

    id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            nullable=False,
            primary_key=True,
            default=uuid.uuid4
        )
    )
    author_id: uuid.UUID = Field(
        description="User ID of the comment author"
    )
    content: str = Field(
        min_length=1,
        max_length=500,
        description="Content of the comment."
    )
    total_likes: int = Field(
        default=0,
        ge=0,
        description="Number of likes on the comment"
    )
    post_uid: uuid.UUID = Field(
        foreign_key="posts.uid",
        description="Reference to the post this comment belongs to"
    )
    created_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP, default=datetime.now),
        default_factory=datetime.now
    )
    updated_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP, default=datetime.now, onupdate=datetime.now),
        default_factory=datetime.now
    )
    post: Optional["Post"] = Relationship(back_populates="comments")





class Post(SQLModel, table=True):
    __tablename__ = "posts"

    uid: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            nullable=False,
            primary_key=True,
            default=uuid.uuid4
        )
    )
    
    author_uid: uuid.UUID = Field(
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
    
    comments: Optional[List[Comment]] = Relationship(back_populates="post")
    
    total_likes: int = Field(
        default=0,
        ge=0,
        description="Number of likes on the post"
    )
    
    images: Optional[str] = Field(
        default=None,
        description="URL to post images"
    )
    
    created_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP, default=datetime.now),
        default_factory=datetime.now
    )
    
    updated_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP, default=datetime.now, onupdate=datetime.now),
        default_factory=datetime.now
    )