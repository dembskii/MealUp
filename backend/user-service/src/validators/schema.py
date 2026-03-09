from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date
from typing import Optional, List, Literal
from uuid import UUID



#Meal record schema helpers
class StructRecordSchema(BaseModel):
    """Schema for individual meal record"""
    recipe_id: str = Field(description = "Recipe ID")
    capacity: float = Field(gt = 0, description = "Portion size")
    time_of_day: Literal["breakfast", "lunch", "dinner", "snack"] = Field(description = "Time of consumption (breakfast/lunch/dinner/snack)")
    created_at: datetime = Field(description = "Creation timestamp")
    updated_at: datetime = Field(description = "Update timestamp")

class DayRecordSchema(BaseModel):
    """Schema for daily meal record"""
    id: UUID = Field(description = "Unique daily record ID")
    records: List[StructRecordSchema] = Field(description = "List of meals consumed")
    total_macro: Optional[dict] = Field(default = None, description = "Aggregated macros for the day")
    created_at: datetime = Field(description = "Creation timestamp")
    updated_at: datetime = Field(description = "Update timestamp")



#Body parameters schema helper
class BodyParamsSchema(BaseModel):
    weight: Optional[float] = Field(gt = 0, default = None, description = "User's weight")
    weight_unit: Literal["kg", "lb"] = Field(default = "kg", description = "User's weight units")
    height: Optional[float] = Field(gt = 0, default = None, description = "User's height")
    height_unit: Literal["cm", "m", "ft"] = Field(default = "cm", description = "User's height unit")


class UserCreate(BaseModel):
    """Schema for creating a user"""
    email: EmailStr = Field(max_length = 40, examples = ["example@mail.com"], description = "User's email")
    username: str = Field(max_length = 40, examples = ["JohnnyHunter"], description = "User's username")
    first_name: str = Field(max_length = 50, examples = ["John"], description = "User's first name")
    last_name: str = Field(max_length = 50, examples = ["Doe"], description = "User's last name")
    date_of_birth: Optional[date] = Field(examples = ["02.02.2025"], description = "User's date of birth", default = None)


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    first_name: Optional[str] = Field(max_length = 50, examples = ["John"], description = "User's first name", default = None)
    last_name: Optional[str] = Field(max_length = 50, examples = ["Doe"], description = "User's last name", default = None)
    date_of_birth: Optional[date] = Field(examples = ["02.02.2025"], description = "User's date of birth", default = None)
    sex: Optional[Literal["male", "female"]] = Field(examples = ["male"], description = "User's sex", default = None)
    age: Optional[int] = Field(examples = [22], description = "User's age", default = None)
    body_params: Optional[BodyParamsSchema] = Field(description = "User's body parameters", default = None)
    username: Optional[str] = Field(max_length = 40, examples = ["JohnnyHunter"], description = "User's username", default = None)
    recipe_ids: Optional[List[str]] = Field(description="List of recipe IDs", default = None)
    meal_records: Optional[List[DayRecordSchema]] = Field(description = "Daily meal records", default = None) 


class UserResponse(BaseModel):
    """Schema for user response"""
    uid: UUID = Field(description = "Unique UUID for the user.")
    auth0_sub: str = Field(description = "Unique Auth0 ID of the user from external authorization provider.")
    email: EmailStr = Field(max_length = 40, examples = ["example@mail.com"], description = "User's email")
    username: str = Field(max_length = 40, examples = ["JohnnyHunter"], description = "User's username")
    first_name: str = Field(max_length = 50, examples = ["John"], description = "User's first name")
    last_name: str = Field(max_length = 50, examples = ["Doe"], description = "User's last name")
    date_of_birth: Optional[date] = Field(examples = ["02.02.2025"], description = "User's date of birth", default = None)
    role: str = Field(examples = ["user"], description = "User's role")
    sex: Optional[str] = Field(examples = ["male"], description = "User's sex", default = None)
    age: Optional[int] = Field(examples = [22], description = "User's age", default = None)
    body_params: Optional[BodyParamsSchema] = Field(description = "User's body parameters", default = None)
    recipe_ids: Optional[List[str]] = Field(description="List of recipe IDs", default = None)
    meal_records: Optional[List[DayRecordSchema]] = Field(description = "Daily meal records", default = None) 
    created_at: datetime = Field(description = "Creation timestamp")
    update_at: datetime = Field(description = "Update timestamp")
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Schema for list of users"""
    total: int = Field(description = "Total amount of existing users.")
    items: list[UserResponse] = Field(description = "Items")


class ErrorResponse(BaseModel):
    """Schema for error response"""
    detail: str = Field(description = "Details of an error.")
    status_code: int = Field(description = "Status code display for error purposes.")


# =================== Liked Workout Schemas =================== #

class LikeWorkoutRequest(BaseModel):
    """Schema for liking/unliking a workout"""
    workout_id: str = Field(
        description="Workout ID from MongoDB workout-service",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )


class LikedWorkoutResponse(BaseModel):
    """Schema for a single liked workout"""
    id: UUID = Field(description="Liked workout record ID")
    user_id: UUID = Field(description="User UID")
    workout_id: str = Field(description="Workout ID from MongoDB")
    created_at: datetime = Field(description="When the workout was liked")

    class Config:
        from_attributes = True


class LikedWorkoutListResponse(BaseModel):
    """Schema for list of liked workouts"""
    total: int = Field(description="Total number of liked workouts")
    items: List[LikedWorkoutResponse] = Field(description="Liked workout items")


class WorkoutLikeStatusResponse(BaseModel):
    """Schema for checking if a workout is liked"""
    workout_id: str = Field(description="Workout ID")
    is_liked: bool = Field(description="Whether the workout is liked by the user")


class BulkLikeCheckRequest(BaseModel):
    """Schema for checking like status of multiple workouts"""
    workout_ids: List[str] = Field(
        description="List of workout IDs to check",
        min_length=1,
        max_length=100
    )


class BulkLikeCheckResponse(BaseModel):
    """Schema for bulk like status check"""
    results: dict[str, bool] = Field(
        description="Map of workout_id to is_liked status"
    )


# =================== Liked Recipe Schemas =================== #

class LikeRecipeRequest(BaseModel):
    """Schema for liking/unliking a recipe"""
    recipe_id: str = Field(
        description="Recipe ID from MongoDB recipe-service",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )


class LikedRecipeResponse(BaseModel):
    """Schema for a single liked recipe"""
    id: UUID = Field(description="Liked recipe record ID")
    user_id: UUID = Field(description="User UID")
    recipe_id: str = Field(description="Recipe ID from MongoDB")
    created_at: datetime = Field(description="When the recipe was liked")

    class Config:
        from_attributes = True


class LikedRecipeListResponse(BaseModel):
    """Schema for list of liked recipes"""
    total: int = Field(description="Total number of liked recipes")
    items: List[LikedRecipeResponse] = Field(description="Liked recipe items")


class RecipeLikeStatusResponse(BaseModel):
    """Schema for checking if a recipe is liked"""
    recipe_id: str = Field(description="Recipe ID")
    is_liked: bool = Field(description="Whether the recipe is liked by the user")


class BulkRecipeLikeCheckRequest(BaseModel):
    """Schema for checking like status of multiple recipes"""
    recipe_ids: List[str] = Field(
        description="List of recipe IDs to check",
        min_length=1,
        max_length=100
    )


class BulkRecipeLikeCheckResponse(BaseModel):
    """Schema for bulk recipe like status check"""
    results: dict[str, bool] = Field(
        description="Map of recipe_id to is_liked status"
    )
