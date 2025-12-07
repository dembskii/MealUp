from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from enum import Enum
from datetime import datetime
import uuid


# ============ ENUMS ============

class BodyPart(str, Enum):
    """Enum for body parts targeted by exercises"""
    CHEST = "chest"
    BACK = "back"
    SHOULDERS = "shoulders"
    BICEPS = "biceps"
    TRICEPS = "triceps"
    FOREARMS = "forearms"
    ABS = "abs"
    OBLIQUES = "obliques"
    QUADRICEPS = "quadriceps"
    HAMSTRINGS = "hamstrings"
    GLUTES = "glutes"
    CALVES = "calves"
    FULL_BODY = "full_body"
    CARDIO = "cardio"


class Advancement(str, Enum):
    """Enum for exercise difficulty level"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ExerciseCategory(str, Enum):
    """Enum for exercise categories"""
    STRENGTH = "strength"
    CARDIO = "cardio"
    FLEXIBILITY = "flexibility"
    BALANCE = "balance"
    PLYOMETRIC = "plyometric"
    CALISTHENICS = "calisthenics"
    OLYMPIC_LIFTING = "olympic_lifting"
    POWERLIFTING = "powerlifting"
    HIIT = "hiit"
    YOGA = "yoga"
    STRETCHING = "stretching"


class TrainingType(str, Enum):
    """Enum for training session types"""
    PUSH = "push"
    PULL = "pull"
    LEGS = "legs"
    UPPER = "upper"
    LOWER = "lower"
    FULL_BODY = "full_body"
    CARDIO = "cardio"
    HIIT = "hiit"
    STRENGTH = "strength"
    HYPERTROPHY = "hypertrophy"
    ENDURANCE = "endurance"
    FLEXIBILITY = "flexibility"
    CUSTOM = "custom"


class SetUnit(str, Enum):
    """Enum for set measurement units"""
    REPS = "reps"           # Number of repetitions
    SECONDS = "seconds"     # Time in seconds (for holds, planks)
    MINUTES = "minutes"     # Time in minutes
    METERS = "meters"       # Distance in meters
    KILOMETERS = "km"       # Distance in kilometers
    CALORIES = "calories"   # Calories burned


class DayOfWeek(int, Enum):
    """ISO 8601 day of week (1-7, Monday to Sunday)"""
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


# ============ EMBEDDED MODELS ============

class StructSet(BaseModel):
    """Structure for a single set within an exercise"""
    volume: float = Field(..., gt=0, description="Volume/amount for the set")
    units: SetUnit = Field(..., description="Unit of measurement for the set")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "volume": 12.0,
                "units": "reps"
            }
        }
    )


class TrainingExercise(BaseModel):
    """Exercise entry within a training session"""
    exercise_id: str = Field(..., description="Reference to Exercise document ID")
    sets: List[StructSet] = Field(..., min_length=1, description="List of sets for this exercise")
    rest_between_sets: Optional[int] = Field(60, ge=0, description="Rest time between sets in seconds")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes for this exercise")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "exercise_id": "550e8400-e29b-41d4-a716-446655440000",
                "sets": [
                    {"volume": 12, "units": "reps"},
                    {"volume": 10, "units": "reps"},
                    {"volume": 8, "units": "reps"}
                ],
                "rest_between_sets": 90,
                "notes": "Focus on slow eccentric"
            }
        }
    )


# ============ EXERCISE MODEL ============

class Exercise(BaseModel):
    """Exercise document stored in MongoDB"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id", description="Unique exercise ID")
    name: str = Field(..., min_length=1, max_length=100, description="Exercise name")
    body_part: BodyPart = Field(..., description="Primary body part targeted")
    advancement: Advancement = Field(..., description="Difficulty level")
    category: ExerciseCategory = Field(..., description="Exercise category")
    description: Optional[str] = Field(None, max_length=1000, description="Exercise description")
    hints: Optional[List[str]] = Field(None, description="Tips and hints for proper form")
    image: Optional[str] = Field(None, description="URL to exercise image")
    video_url: Optional[str] = Field(None, description="URL to demonstration video")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="_created_at")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="_updated_at")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Barbell Bench Press",
                "body_part": "chest",
                "advancement": "intermediate",
                "category": "strength",
                "description": "A compound exercise targeting the chest, shoulders, and triceps",
                "hints": [
                    "Keep feet flat on the floor",
                    "Retract shoulder blades",
                    "Lower bar to mid-chest"
                ],
                "image": "https://example.com/bench-press.jpg"
            }
        }
    )


class ExerciseCreate(BaseModel):
    """Schema for creating a new exercise"""
    name: str = Field(..., min_length=1, max_length=100)
    body_part: BodyPart
    advancement: Advancement
    category: ExerciseCategory
    description: Optional[str] = Field(None, max_length=1000)
    hints: Optional[List[str]] = None
    image: Optional[str] = None
    video_url: Optional[str] = None


class ExerciseUpdate(BaseModel):
    """Schema for updating an exercise"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    body_part: Optional[BodyPart] = None
    advancement: Optional[Advancement] = None
    category: Optional[ExerciseCategory] = None
    description: Optional[str] = Field(None, max_length=1000)
    hints: Optional[List[str]] = None
    image: Optional[str] = None
    video_url: Optional[str] = None


class ExerciseResponse(BaseModel):
    """Response schema for exercise"""
    id: str = Field(alias="_id")
    name: str
    body_part: BodyPart
    advancement: Advancement
    category: ExerciseCategory
    description: Optional[str] = None
    hints: Optional[List[str]] = None
    image: Optional[str] = None
    video_url: Optional[str] = None
    created_at: datetime = Field(alias="_created_at")
    updated_at: datetime = Field(alias="_updated_at")

    model_config = ConfigDict(populate_by_name=True)


# ============ TRAINING MODEL ============

class Training(BaseModel):
    """Training session document stored in MongoDB"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id", description="Unique training ID")
    name: str = Field(..., min_length=1, max_length=100, description="Training session name")
    exercises: List[TrainingExercise] = Field(..., min_length=1, description="List of exercises in this training")
    est_time: int = Field(..., gt=0, description="Estimated time in seconds")
    day: DayOfWeek = Field(..., description="Day of the week (ISO 8601: 1-7)")
    training_type: TrainingType = Field(..., description="Type of training session")
    description: Optional[str] = Field(None, max_length=500, description="Training description")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="_created_at")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="_updated_at")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "Push Day A",
                "exercises": [
                    {
                        "exercise_id": "550e8400-e29b-41d4-a716-446655440000",
                        "sets": [
                            {"volume": 12, "units": "reps"},
                            {"volume": 10, "units": "reps"}
                        ],
                        "rest_between_sets": 90
                    }
                ],
                "est_time": 3600,
                "day": 1,
                "training_type": "push"
            }
        }
    )


class TrainingCreate(BaseModel):
    """Schema for creating a new training session"""
    name: str = Field(..., min_length=1, max_length=100)
    exercises: List[TrainingExercise] = Field(..., min_length=1)
    est_time: int = Field(..., gt=0, description="Estimated time in seconds")
    day: DayOfWeek
    training_type: TrainingType
    description: Optional[str] = Field(None, max_length=500)


class TrainingUpdate(BaseModel):
    """Schema for updating a training session"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    exercises: Optional[List[TrainingExercise]] = None
    est_time: Optional[int] = Field(None, gt=0)
    day: Optional[DayOfWeek] = None
    training_type: Optional[TrainingType] = None
    description: Optional[str] = Field(None, max_length=500)


class TrainingResponse(BaseModel):
    """Response schema for training session"""
    id: str = Field(alias="_id")
    name: str
    exercises: List[TrainingExercise]
    est_time: int
    day: DayOfWeek
    training_type: TrainingType
    description: Optional[str] = None
    created_at: datetime = Field(alias="_created_at")
    updated_at: datetime = Field(alias="_updated_at")

    model_config = ConfigDict(populate_by_name=True)


# ============ WORKOUT PLAN MODEL ============

class WorkoutPlan(BaseModel):
    """Workout plan document stored in Mongo DB"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id", description="Unique workout plan ID")
    name: str = Field(..., min_length=1, max_length=100, description="Workout plan name")
    trainer_id: str = Field(..., description="User ID of the trainer/creator")
    clients: List[str] = Field(default=[], description="List of client user IDs")
    trainings: List[str] = Field(default=[], description="List of Training IDs")
    description: Optional[str] = Field(None, max_length=1000, description="Plan description")
    is_public: bool = Field(default=False, description="Whether the plan is publicly visible")
    total_likes: int = Field(default=0, ge=0, description="Total number of likes")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="_created_at")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="_updated_at")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "550e8400-e29b-41d4-a716-446655440002",
                "name": "12-Week Strength Program",
                "trainer_id": "auth0|123456",
                "clients": ["auth0|789012"],
                "trainings": ["550e8400-e29b-41d4-a716-446655440001"],
                "description": "A comprehensive strength building program",
                "is_public": True,
                "total_likes": 42
            }
        }
    )


class WorkoutPlanCreate(BaseModel):
    """Schema for creating a new workout plan"""
    name: str = Field(..., min_length=1, max_length=100)
    clients: Optional[List[str]] = Field(default=[])
    trainings: Optional[List[str]] = Field(default=[])
    description: Optional[str] = Field(None, max_length=1000)
    is_public: bool = Field(default=False)


class WorkoutPlanUpdate(BaseModel):
    """Schema for updating a workout plan"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    clients: Optional[List[str]] = None
    trainings: Optional[List[str]] = None
    description: Optional[str] = Field(None, max_length=1000)
    is_public: Optional[bool] = None


class WorkoutPlanResponse(BaseModel):
    """Response schema for workout plan"""
    id: str = Field(alias="_id")
    name: str
    trainer_id: str
    clients: List[str]
    trainings: List[str]
    description: Optional[str] = None
    is_public: bool
    total_likes: int
    created_at: datetime = Field(alias="_created_at")
    updated_at: datetime = Field(alias="_updated_at")

    model_config = ConfigDict(populate_by_name=True)


# ============ AGGREGATED RESPONSE MODELS ============

class TrainingWithExercises(BaseModel):
    """Training session with full exercise details"""
    id: str = Field(alias="_id")
    name: str
    exercises: List[dict]  # Full exercise data joined
    est_time: int
    day: DayOfWeek
    training_type: TrainingType
    description: Optional[str] = None
    created_at: datetime = Field(alias="_created_at")
    updated_at: datetime = Field(alias="_updated_at")

    model_config = ConfigDict(populate_by_name=True)


class WorkoutPlanDetailed(BaseModel):
    """Workout plan with full training details"""
    id: str = Field(alias="_id")
    name: str
    trainer_id: str
    clients: List[str]
    trainings: List[TrainingWithExercises]
    description: Optional[str] = None
    is_public: bool
    total_likes: int
    created_at: datetime = Field(alias="_created_at")
    updated_at: datetime = Field(alias="_updated_at")

    model_config = ConfigDict(populate_by_name=True)
