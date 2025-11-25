import sqlalchemy.dialects.postgresql as pg
from sqlmodel import SQLModel, Field, Column, Relationship, Enum
from datetime import datetime, date
from typing import Optional, List
from datetime import datetime
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
        sa_column=Column(
            pg.VARCHAR(255),
            nullable=False,
            unique=True,
            index=True
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
    username: str = Field(min_length = 3, max_length = 25, description = "Username for the user.")
    first_name: str = Field(min_length = 3, max_length = 50, default = "First Name", description = "User's first name")
    last_name: str = Field(min_length = 3, max_length = 50, default = "Last Name", description = "User's last name")
    date_of_birth: date = Field(sa_column = Column(pg.DATE, default = None), description = "User's date of birth!")
    created_at: datetime = Field(sa_column = Column(pg.TIMESTAMP, default = datetime.now))
    update_at: datetime = Field(sa_column = Column(pg.TIMESTAMP, default = datetime.now, onupdate = datetime.now))


#Couple of records will be added while developing project
    # recipies
    # posts
    # roles
    # sex
    # age
    # posts_liked
    # comments_liked
    # records
    # optional: profile_pic

def __repr__(self):
    return f"<User {self.username}>"