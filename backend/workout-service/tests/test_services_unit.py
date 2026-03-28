from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.model import (
    Advancement,
    BodyPart,
    ExerciseCategory,
    ExerciseCreate,
    ExerciseUpdate,
    SetUnit,
    StructSet,
    TrainingCreate,
    TrainingExercise,
    TrainingType,
    TrainingUpdate,
    WorkoutPlanCreate,
    WorkoutPlanUpdate,
)
from src.services.exercise_service import ExerciseService
from src.services.training_service import TrainingService
from src.services.workout_plan_service import WorkoutPlanService


def _exercise_doc(ex_id: str = "ex-1") -> dict:
    now = datetime.now(UTC)
    return {
        "_id": ex_id,
        "name": "Push Up",
        "body_part": "chest",
        "advancement": "beginner",
        "category": "strength",
        "description": "desc",
        "hints": [],
        "image": None,
        "video_url": None,
        "_created_at": now,
        "_updated_at": now,
    }


def _training_doc(tr_id: str = "tr-1") -> dict:
    now = datetime.now(UTC)
    return {
        "_id": tr_id,
        "name": "Push",
        "creator_id": "trainer-1",
        "exercises": [
            {
                "exercise_id": "ex-1",
                "sets": [{"volume": 10, "units": "reps"}],
                "rest_between_sets": 60,
                "notes": None,
            }
        ],
        "est_time": 1800,
        "training_type": "push",
        "description": "desc",
        "_created_at": now,
        "_updated_at": now,
    }


def _plan_doc(plan_id: str = "plan-1") -> dict:
    now = datetime.now(UTC)
    return {
        "_id": plan_id,
        "name": "Plan",
        "trainer_id": "trainer-1",
        "clients": [],
        "trainings": [],
        "schedule": None,
        "description": "desc",
        "is_public": False,
        "total_likes": 0,
        "_created_at": now,
        "_updated_at": now,
    }


def _cursor(items):
    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.to_list = AsyncMock(return_value=items)
    return cursor


@pytest.mark.asyncio
async def test_exercise_service_full(monkeypatch: pytest.MonkeyPatch):
    collection = MagicMock()
    collection.insert_one = AsyncMock()
    collection.find_one = AsyncMock(
        side_effect=[_exercise_doc(), _exercise_doc(), _exercise_doc(), None]
    )
    collection.find.return_value = _cursor([_exercise_doc()])
    collection.update_one = AsyncMock()
    delete_ok = MagicMock()
    delete_ok.deleted_count = 1
    delete_no = MagicMock()
    delete_no.deleted_count = 0
    collection.delete_one = AsyncMock(side_effect=[delete_ok, delete_no])
    collection.count_documents = AsyncMock(return_value=3)

    monkeypatch.setattr("src.services.exercise_service.get_database", lambda: {"exercises": collection})

    created = await ExerciseService.create_exercise(
        ExerciseCreate(
            name="Push Up",
            body_part=BodyPart.CHEST,
            advancement=Advancement.BEGINNER,
            category=ExerciseCategory.STRENGTH,
            description=None,
        )
    )
    assert created.name == "Push Up"

    found = await ExerciseService.get_exercise("ex-1")
    assert found is not None

    listed = await ExerciseService.get_exercises(search="push", body_part=BodyPart.CHEST)
    assert len(listed) == 1

    by_ids = await ExerciseService.get_exercises_by_ids(["ex-1"])
    assert len(by_ids) == 1

    updated = await ExerciseService.update_exercise("ex-1", ExerciseUpdate(name="Renamed", description=None))
    assert updated is not None

    missing = await ExerciseService.update_exercise("missing", ExerciseUpdate(name="X", description=None))
    assert missing is None

    assert await ExerciseService.delete_exercise("ex-1") is True
    assert await ExerciseService.delete_exercise("missing") is False
    assert await ExerciseService.count_exercises(category=ExerciseCategory.STRENGTH) == 3


@pytest.mark.asyncio
async def test_exercise_search(monkeypatch: pytest.MonkeyPatch):
    collection = MagicMock()
    collection.find.return_value = _cursor([_exercise_doc("ex-2")])
    monkeypatch.setattr("src.services.exercise_service.get_database", lambda: {"exercises": collection})

    result = await ExerciseService.search_exercises("push", tags=["a"], body_part=BodyPart.CHEST)
    assert len(result) == 1


@pytest.mark.asyncio
async def test_training_service_paths(monkeypatch: pytest.MonkeyPatch):
    collection = MagicMock()
    collection.insert_one = AsyncMock()
    collection.find_one = AsyncMock(
        side_effect=[
            _training_doc(),
            _training_doc(),
            _training_doc(),
            None,
            _training_doc(),
        ]
    )
    collection.find.return_value = _cursor([_training_doc()])
    collection.update_one = AsyncMock()
    del_ok = MagicMock()
    del_ok.deleted_count = 1
    del_no = MagicMock()
    del_no.deleted_count = 0
    collection.delete_one = AsyncMock(side_effect=[del_ok, del_no])
    collection.count_documents = AsyncMock(return_value=2)

    exercises_collection = MagicMock()
    exercises_collection.find_one = AsyncMock(return_value=_exercise_doc())

    monkeypatch.setattr(
        "src.services.training_service.get_database",
        lambda: {"trainings": collection, "exercises": exercises_collection},
    )
    monkeypatch.setattr(
        "src.services.training_service.ExerciseService.get_exercises_by_ids",
        AsyncMock(return_value=[MagicMock()]),
    )

    payload = TrainingCreate(
        name="Push",
        exercises=[
            TrainingExercise(
                exercise_id="ex-1",
                sets=[StructSet(volume=10, units=SetUnit.REPS)],
                rest_between_sets=60,
                notes=None,
            )
        ],
        est_time=1800,
        training_type=TrainingType.PUSH,
        description=None,
    )
    created = await TrainingService.create_training(payload, creator_id="u-1")
    assert created.name == "Push"

    assert (await TrainingService.get_training("tr-1")) is not None
    assert len(await TrainingService.get_trainings()) == 1
    assert len(await TrainingService.get_trainings_by_ids(["tr-1"])) == 1

    updated = await TrainingService.update_training("tr-1", TrainingUpdate(name="U", est_time=1200, description=None))
    assert updated is not None

    none_update = await TrainingService.update_training("missing", TrainingUpdate(name="U", est_time=1200, description=None))
    assert none_update is None

    assert await TrainingService.delete_training("tr-1") is True
    assert await TrainingService.delete_training("missing") is False
    assert await TrainingService.count_trainings() == 2

    detailed = await TrainingService.get_training_with_exercises("tr-1")
    assert detailed is not None


@pytest.mark.asyncio
async def test_training_validation_error(monkeypatch: pytest.MonkeyPatch):
    collection = MagicMock()
    collection.insert_one = AsyncMock()
    monkeypatch.setattr("src.services.training_service.get_database", lambda: {"trainings": collection})
    monkeypatch.setattr("src.services.training_service.ExerciseService.get_exercises_by_ids", AsyncMock(return_value=[]))

    payload = TrainingCreate(
        name="Push",
        exercises=[
            TrainingExercise(
                exercise_id="missing",
                sets=[StructSet(volume=10, units=SetUnit.REPS)],
                rest_between_sets=60,
                notes=None,
            )
        ],
        est_time=1800,
        training_type=TrainingType.PUSH,
        description=None,
    )
    with pytest.raises(ValueError):
        await TrainingService.create_training(payload)


@pytest.mark.asyncio
async def test_training_update_validation_and_with_exercises_list(monkeypatch: pytest.MonkeyPatch):
    collection = MagicMock()
    collection.find_one = AsyncMock(side_effect=[_training_doc(), _training_doc()])
    collection.update_one = AsyncMock()
    monkeypatch.setattr(
        "src.services.training_service.get_database",
        lambda: {"trainings": collection, "exercises": MagicMock()},
    )
    monkeypatch.setattr(
        "src.services.training_service.ExerciseService.get_exercises_by_ids",
        AsyncMock(return_value=[]),
    )

    with pytest.raises(ValueError):
        await TrainingService.update_training(
            "tr-1",
            TrainingUpdate(
                name="Upd",
                exercises=[
                    TrainingExercise(
                        exercise_id="missing",
                        sets=[StructSet(volume=10, units=SetUnit.REPS)],
                        rest_between_sets=60,
                        notes=None,
                    )
                ],
                est_time=1000,
                description=None,
            ),
        )

    monkeypatch.setattr(
        "src.services.training_service.TrainingService.get_training_with_exercises",
        AsyncMock(side_effect=[MagicMock(), None]),
    )
    result = await TrainingService.get_trainings_with_exercises(["a", "b"])
    assert len(result) == 1


@pytest.mark.asyncio
async def test_workout_plan_service_paths(monkeypatch: pytest.MonkeyPatch):
    collection = MagicMock()
    collection.insert_one = AsyncMock()
    collection.find_one = AsyncMock(
        side_effect=[
            _plan_doc(),
            _plan_doc(),
            _plan_doc(),
            _plan_doc(),
            _plan_doc(),
            _plan_doc(),
            _plan_doc(),
            {**_plan_doc(), "clients": ["c1"]},
            _plan_doc(),
            {**_plan_doc(), "trainings": ["tr-1"]},
            _plan_doc(),
            _plan_doc(),
                _plan_doc(),
        ]
    )
    collection.find.return_value = _cursor([_plan_doc()])
    collection.update_one = AsyncMock()
    del_ok = MagicMock()
    del_ok.deleted_count = 1
    collection.delete_one = AsyncMock(return_value=del_ok)
    collection.find_one_and_update = AsyncMock(side_effect=[{**_plan_doc(), "total_likes": 1}, _plan_doc()])
    collection.count_documents = AsyncMock(return_value=7)

    monkeypatch.setattr("src.services.workout_plan_service.get_database", lambda: {"workout_plans": collection})
    monkeypatch.setattr("src.services.workout_plan_service.TrainingService.get_trainings_by_ids", AsyncMock(return_value=[MagicMock()]))
    monkeypatch.setattr("src.services.workout_plan_service.TrainingService.get_training", AsyncMock(return_value=MagicMock()))
    monkeypatch.setattr("src.services.workout_plan_service.TrainingService.get_trainings_with_exercises", AsyncMock(return_value=[]))

    created = await WorkoutPlanService.create_workout_plan(
        "trainer-1",
        WorkoutPlanCreate(name="Plan", trainings=["tr-1"], clients=[], description=None),
    )
    assert created.name == "Plan"

    assert (await WorkoutPlanService.get_workout_plan("plan-1")) is not None
    assert len(await WorkoutPlanService.get_workout_plans()) == 1
    assert len(await WorkoutPlanService.get_workout_plans_by_ids(["plan-1"])) == 1

    updated = await WorkoutPlanService.update_workout_plan(
        "plan-1", WorkoutPlanUpdate(name="U", description=None), trainer_id="trainer-1"
    )
    assert updated is not None

    assert await WorkoutPlanService.delete_workout_plan("plan-1", trainer_id="trainer-1") is True

    added_client = await WorkoutPlanService.add_client_to_plan("plan-1", "c1", trainer_id="trainer-1")
    assert added_client is not None
    assert added_client is not None

    removed_client = await WorkoutPlanService.remove_client_from_plan("plan-1", "c1", trainer_id="trainer-1")
    assert removed_client is not None
    assert removed_client is not None

    added_training = await WorkoutPlanService.add_training_to_plan("plan-1", "tr-1", trainer_id="trainer-1")
    assert added_training is not None
    assert added_training is not None

    removed_training = await WorkoutPlanService.remove_training_from_plan("plan-1", "tr-1", trainer_id="trainer-1")
    assert removed_training is not None
    assert removed_training is not None

    liked = await WorkoutPlanService.like_workout_plan("plan-1")
    assert liked is not None
    assert liked.total_likes == 1

    unliked = await WorkoutPlanService.unlike_workout_plan("plan-1")
    assert unliked is not None
    assert unliked.total_likes == 0

    assert await WorkoutPlanService.count_workout_plans(is_public=False) == 7
    assert (await WorkoutPlanService.get_workout_plan_detailed("plan-1")) is not None


@pytest.mark.asyncio
async def test_workout_plan_permission_and_validation_errors(monkeypatch: pytest.MonkeyPatch):
    collection = MagicMock()
    collection.find_one = AsyncMock(return_value={**_plan_doc(), "trainer_id": "owner-1"})
    monkeypatch.setattr("src.services.workout_plan_service.get_database", lambda: {"workout_plans": collection})

    with pytest.raises(PermissionError):
        await WorkoutPlanService.update_workout_plan(
            "plan-1", WorkoutPlanUpdate(name="U", description=None), trainer_id="intruder"
        )

    with pytest.raises(PermissionError):
        await WorkoutPlanService.delete_workout_plan("plan-1", trainer_id="intruder")


@pytest.mark.asyncio
async def test_workout_plan_more_error_paths(monkeypatch: pytest.MonkeyPatch):
    base = _plan_doc()
    collection = MagicMock()
    collection.find_one = AsyncMock(return_value={**base, "trainer_id": "owner-1"})
    monkeypatch.setattr("src.services.workout_plan_service.get_database", lambda: {"workout_plans": collection})

    with pytest.raises(PermissionError):
        await WorkoutPlanService.add_client_to_plan("p1", "c1", trainer_id="intruder")
    with pytest.raises(PermissionError):
        await WorkoutPlanService.remove_client_from_plan("p1", "c1", trainer_id="intruder")
    with pytest.raises(PermissionError):
        await WorkoutPlanService.add_training_to_plan("p1", "t1", trainer_id="intruder")
    with pytest.raises(PermissionError):
        await WorkoutPlanService.remove_training_from_plan("p1", "t1", trainer_id="intruder")


@pytest.mark.asyncio
async def test_workout_plan_none_paths(monkeypatch: pytest.MonkeyPatch):
    collection = MagicMock()
    collection.find_one = AsyncMock(return_value=None)
    monkeypatch.setattr("src.services.workout_plan_service.get_database", lambda: {"workout_plans": collection})

    assert await WorkoutPlanService.delete_workout_plan("missing") is False
    assert await WorkoutPlanService.add_client_to_plan("missing", "c1") is None
    assert await WorkoutPlanService.remove_client_from_plan("missing", "c1") is None
    assert await WorkoutPlanService.add_training_to_plan("missing", "t1") is None
    assert await WorkoutPlanService.remove_training_from_plan("missing", "t1") is None


@pytest.mark.asyncio
async def test_workout_plan_training_missing_and_helpers(monkeypatch: pytest.MonkeyPatch):
    collection = MagicMock()
    collection.find_one = AsyncMock(return_value=_plan_doc())
    collection.find.return_value = _cursor([_plan_doc()])
    monkeypatch.setattr("src.services.workout_plan_service.get_database", lambda: {"workout_plans": collection})
    monkeypatch.setattr("src.services.workout_plan_service.TrainingService.get_training", AsyncMock(return_value=None))

    with pytest.raises(ValueError):
        await WorkoutPlanService.add_training_to_plan("p1", "missing", trainer_id="trainer-1")

    plans = await WorkoutPlanService.get_trainer_plans("trainer-1", skip=0, limit=10)
    assert len(plans) == 1

    client_plans = await WorkoutPlanService.get_client_plans("client-1", skip=0, limit=10)
    assert len(client_plans) == 1


@pytest.mark.asyncio
async def test_workout_plan_invalid_training(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("src.services.workout_plan_service.get_database", lambda: {"workout_plans": MagicMock()})
    monkeypatch.setattr("src.services.workout_plan_service.TrainingService.get_trainings_by_ids", AsyncMock(return_value=[]))

    with pytest.raises(ValueError):
        await WorkoutPlanService.create_workout_plan(
            "trainer-1", WorkoutPlanCreate(name="P", trainings=["bad"], clients=[], description=None)
        )
