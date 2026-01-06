import sqlalchemy.dialects.postgresql as pg
from sqlmodel import SQLModel, Field, Column
from datetime import datetime, timezone
from sqlalchemy import UniqueConstraint
import uuid


class CommentLike(SQLModel, table=True):
    """Model for likes on comments"""
    __tablename__ = "comment_likes"

    id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            nullable=False,
            primary_key=True,
            default=uuid.uuid4
        )
    )

    user_id: uuid.UUID = Field(
        description="User ID who liked the comment"
    )

    comment_id: uuid.UUID = Field(
        foreign_key="comments.id",
        description="Reference to the liked comment"
    )

    created_at: datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            nullable=False,
            default=lambda: datetime.now(timezone.utc)
        ),
        default_factory=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint('user_id', 'comment_id', name='uq_user_comment_like'),
    )