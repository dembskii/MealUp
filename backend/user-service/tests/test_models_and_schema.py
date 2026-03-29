from datetime import datetime, timezone

from src.models import model
from src.models.model import BodyParams, DayRecord, StructRecord, TimeOfDay, User
from src.validators.schema import (
    BodyParamsSchema,
    BulkLikeCheckRequest,
    BulkRecipeLikeCheckRequest,
    LikeRecipeRequest,
    LikeWorkoutRequest,
    StructRecordSchema,
    UserCreate,
    UserUpdate,
)


def test_model_helpers_and_repr():
    record = StructRecord(recipe_id="r1", capacity=1.5, time_of_day=TimeOfDay.BREAKFAST)
    day = DayRecord(records=[record])
    params = BodyParams(weight=75.0, height=180.0)

    user = User(
        auth0_sub="auth0|abc",
        email="john@example.com",
        username="johnny",
        first_name="John",
        last_name="Doe",
        body_params=params,
        meal_records=[day],
    )

    rendered = model.__repr__(user)
    assert "johnny" in rendered
    assert "auth0|abc" in rendered


def test_schema_models_validation():
    now = datetime.now(timezone.utc)

    create = UserCreate(
        email="john@example.com",
        username="johnny",
        first_name="John",
        last_name="Doe",
    )
    assert create.username == "johnny"

    update = UserUpdate(first_name="Jane", recipe_ids=["r1", "r2"])
    assert update.first_name == "Jane"

    struct = StructRecordSchema(
        recipe_id="r1",
        capacity=1.0,
        time_of_day="breakfast",
        created_at=now,
        updated_at=now,
    )
    assert struct.recipe_id == "r1"

    body = BodyParamsSchema(weight=80.0, height=182.0)
    assert body.weight_unit == "kg"

    like_workout = LikeWorkoutRequest(workout_id="w1")
    like_recipe = LikeRecipeRequest(recipe_id="r1")
    bulk_workout = BulkLikeCheckRequest(workout_ids=["w1"])
    bulk_recipe = BulkRecipeLikeCheckRequest(recipe_ids=["r1"])

    assert like_workout.workout_id == "w1"
    assert like_recipe.recipe_id == "r1"
    assert bulk_workout.workout_ids == ["w1"]
    assert bulk_recipe.recipe_ids == ["r1"]
