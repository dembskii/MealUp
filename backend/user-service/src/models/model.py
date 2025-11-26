import sqlalchemy.dialects.postgresql as pg
from sqlmodel import SQLModel, Field, Column
from datetime import datetime, date
from typing import Optional, List
from enum import Enum
from pydantic import EmailStr
import uuid


class UserRole(str, Enum):
    USER = "user"
    TRAINER = "trainer"
    ADMIN = "admin"

class UserSex(str, Enum):
    MALE = "male"
    FEMALE = "female"


class User(SQLModel, table = True):
    __tablename__ = "users"
    
    uid: uuid.UUID = Field(
        sa_column = Column(
            pg.UUID,
            nullable = False,
            primary_key = True,
            default = uuid.uuid4
    ))
    auth0_sub: str = Field(
        sa_column = Column(
            pg.VARCHAR(255),
            nullable = False,
            unique = True,
            index = True
        ),
        description="Unique ID from Auth0 (sub claim)"
    )
    email: EmailStr = Field(
        sa_column = Column(
            pg.VARCHAR(255),
            nullable = False,
            unique = True,
            index = True
        ),
        description="Email address of the user",
    )
    username: str = Field(
        min_length = 3,
        max_length = 25,
        description = "Username for the user."
    )
    first_name: str = Field(
        min_length = 3,
        max_length = 50,
        default = "First Name",
        description = "User's first name"
    )
    last_name: str = Field(
        min_length = 3,
        max_length = 50,
        default = "Last Name",
        description = "User's last name"
    )
    date_of_birth: Optional[date] = Field(
        sa_column = Column(pg.DATE, nullable = True),
        default = None,
        description = "User's date of birth!"
    )
    role: UserRole = Field(
        sa_column = Column(pg.VARCHAR(50), default = UserRole.USER),
        default = UserRole.USER,
        description = "User role"
    )
    sex: Optional[UserSex] = Field(
        sa_column = Column(pg.VARCHAR(50), nullable = True),
        default = None,
        description = "User sex"
    )
    created_at: datetime = Field(
        sa_column = Column(pg.TIMESTAMP, default = datetime.now),
        default_factory = datetime.now
    )
    update_at: datetime = Field(
        sa_column = Column(pg.TIMESTAMP, default = datetime.now, onupdate = datetime.now),
        default_factory = datetime.now
    )


def __repr__(self):
    return f"<User {self.username} ({self.auth0_sub})>"