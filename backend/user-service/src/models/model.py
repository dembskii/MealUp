import sqlalchemy.dialects.postgresql as pg
from sqlmodel import SQLModel, Field, Column
from datetime import datetime, date, timezone
from typing import Optional, List
from enum import Enum
from pydantic import EmailStr
from sqlalchemy import UniqueConstraint
import uuid



#User Role Enum
class UserRole(str, Enum):
    USER = "user"
    TRAINER = "trainer"
    ADMIN = "admin"

#User Sex Enum
class UserSex(str, Enum):
    MALE = "male"
    FEMALE = "female"


#Body Params Enum
class WeightUnit(str, Enum):
    KG = "kg"
    LB = "lb"

class HeightUnit(str, Enum):
    CM = "cm"
    M = "m"
    FT = "ft"


#Record Enum
class TimeOfDay(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"



class StructRecord(SQLModel):
    """Individual record of a meal"""
    recipe_id: str = Field(
        description = "Recipe ID"
    )
    capacity: float = Field(
        gt = 0,
        description = "Portion size"
    )
    time_of_day: TimeOfDay = Field(
        description = "Time of consumption"
    )
    created_at: datetime = Field(
        default_factory = datetime.now
    )
    updated_at: datetime = Field(
        default_factory = datetime.now
    )


class DayRecord(SQLModel):
    """Daily record of consumed meals"""
    id: uuid.UUID = Field(
        default_factory = uuid.uuid4
    )
    records: List[StructRecord] = Field(
        default_factory = list,
        description = "List of meals consumed")
    total_macro: Optional[dict] = Field(
        default = None,
        description = "Aggregated total macros for the day"
    )
    created_at: datetime = Field(
        default_factory = datetime.now
    )
    updated_at: datetime = Field(
        default_factory = datetime.now
    ) 



class BodyParams(SQLModel):
    """Body parameters - embedded in User"""
    weight: Optional[float] = Field(
        gt = 0, default = None
    )
    weight_unit: Optional[WeightUnit] = Field(
        default = WeightUnit.KG
    )
    height: Optional[float] = Field(
        gt = 0,
        default = None
    )
    height_unit: Optional[HeightUnit] = Field(
        default = HeightUnit.CM
    )



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
        description = "Unique ID from Auth0 (sub claim)"
    )
    email: EmailStr = Field(
        sa_column = Column(
            pg.VARCHAR(255),
            nullable = False,
            unique = True,
            index = True
        ),
        description = "Email address of the user",
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
    age: Optional[int] = Field(
        sa_column = Column(pg.INTEGER, nullable = True),
        default = None,
        description = "User age"
    )
    body_params: Optional[BodyParams] = Field(
        sa_column = Column(pg.JSON, nullable = True),
        default = None,
        description = "User's body parameters"
    )
    recipe_ids: Optional[List[str]] = Field(
        sa_column = Column(pg.JSON, nullable = True),
        default = None,
        description = "List of recipe IDs from Recipe Service"
    )
    meal_records: Optional[List[DayRecord]] = Field(
        sa_column = Column(pg.JSON, nullable = True),
        default = None,
        description = "Daily meal records"
    )
    created_at: datetime = Field(
        sa_column = Column(pg.TIMESTAMP, default = datetime.now),
        default_factory = datetime.now
    )
    update_at: datetime = Field(
        sa_column = Column(pg.TIMESTAMP, default = datetime.now, onupdate = datetime.now),
        default_factory = datetime.now
    )

#To be added:
# Posts
# PostsLiked
# CommentsLiked
# Records



def __repr__(self):
    return f"<User {self.username} ({self.auth0_sub})>"


class LikedWorkout(SQLModel, table=True):
    """Tracks which users liked which workouts"""
    __tablename__ = "liked_workouts"

    id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            nullable=False,
            primary_key=True,
            default=uuid.uuid4
        )
    )

    user_id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            nullable=False,
            index=True
        ),
        description="User UID who liked the workout"
    )

    workout_id: str = Field(
        sa_column=Column(
            pg.VARCHAR(255),
            nullable=False,
            index=True
        ),
        description="Workout ID from MongoDB workout-service"
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
        UniqueConstraint('user_id', 'workout_id', name='uq_user_workout_like'),
    )


class LikedRecipe(SQLModel, table=True):
    """Tracks which users liked which recipes"""
    __tablename__ = "liked_recipes"

    id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            nullable=False,
            primary_key=True,
            default=uuid.uuid4
        )
    )

    user_id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            nullable=False,
            index=True
        ),
        description="User UID who liked the recipe"
    )

    recipe_id: str = Field(
        sa_column=Column(
            pg.VARCHAR(255),
            nullable=False,
            index=True
        ),
        description="Recipe ID from MongoDB recipe-service"
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
        UniqueConstraint('user_id', 'recipe_id', name='uq_user_recipe_like'),
    )