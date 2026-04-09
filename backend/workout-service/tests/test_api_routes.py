from datetime import datetime, UTC
from unittest.mock import AsyncMock

from src.services.exercise_service import ExerciseService
from src.services.training_service import TrainingService
from src.services.workout_plan_service import WorkoutPlanService


def _exercise_dict(exercise_id: str = "ex-1") -> dict:
    now = datetime.now(UTC)
    return {
        "_id": exercise_id,
        "name": "Push Up",
        "body_part": "chest",
        "advancement": "beginner",
        "category": "strength",
        "description": "Classic push exercise",
        "hints": [],
        "image": None,
        "video_url": None,
        "_created_at": now.isoformat(),
        "_updated_at": now.isoformat(),
    }


def _training_dict(training_id: str = "tr-1") -> dict:
    now = datetime.now(UTC)
    return {
        "_id": training_id,
        "name": "Push Day",
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
        "_created_at": now.isoformat(),
        "_updated_at": now.isoformat(),
    }


def _plan_dict(plan_id: str = "plan-1") -> dict:
    now = datetime.now(UTC)
    return {
        "_id": plan_id,
        "name": "Plan A",
        "trainer_id": "trainer-1",
        "clients": [],
        "trainings": [],
        "schedule": None,
        "description": "desc",
        "is_public": False,
        "total_likes": 0,
        "_created_at": now.isoformat(),
        "_updated_at": now.isoformat(),
    }


def test_root_and_health(client):
    assert client.get("/").status_code == 200
    assert client.get("/health").status_code == 200


def test_get_exercises_success(client, monkeypatch):
    monkeypatch.setattr(ExerciseService, "get_exercises", AsyncMock(return_value=[_exercise_dict()]))
    response = client.get("/workouts/exercises")
    assert response.status_code == 200
    assert response.json()[0]["_id"] == "ex-1"


def test_get_exercises_error(client, monkeypatch):
    monkeypatch.setattr(ExerciseService, "get_exercises", AsyncMock(side_effect=RuntimeError("boom")))
    response = client.get("/workouts/exercises")
    assert response.status_code == 500


def test_get_exercise_found_and_missing(client, monkeypatch):
    monkeypatch.setattr(ExerciseService, "get_exercise", AsyncMock(return_value=_exercise_dict("ex-2")))
    assert client.get("/workouts/exercises/ex-2").status_code == 200

    monkeypatch.setattr(ExerciseService, "get_exercise", AsyncMock(return_value=None))
    assert client.get("/workouts/exercises/missing").status_code == 404


def test_create_exercise_success_and_error(client, monkeypatch):
    monkeypatch.setattr(ExerciseService, "create_exercise", AsyncMock(return_value=_exercise_dict()))
    ok = client.post(
        "/workouts/exercises",
        json={
            "name": "Push Up",
            "body_part": "chest",
            "advancement": "beginner",
            "category": "strength",
        },
    )
    assert ok.status_code == 201

    monkeypatch.setattr(ExerciseService, "create_exercise", AsyncMock(side_effect=RuntimeError("boom")))
    err = client.post(
        "/workouts/exercises",
        json={
            "name": "Push Up",
            "body_part": "chest",
            "advancement": "beginner",
            "category": "strength",
        },
    )
    assert err.status_code == 500


def test_update_and_delete_exercise(client, monkeypatch):
    monkeypatch.setattr(ExerciseService, "update_exercise", AsyncMock(return_value=_exercise_dict()))
    assert client.put("/workouts/exercises/ex-1", json={"name": "New"}).status_code == 200

    monkeypatch.setattr(ExerciseService, "update_exercise", AsyncMock(return_value=None))
    assert client.put("/workouts/exercises/missing", json={"name": "New"}).status_code == 404

    monkeypatch.setattr(ExerciseService, "delete_exercise", AsyncMock(return_value=True))
    assert client.delete("/workouts/exercises/ex-1").status_code == 204

    monkeypatch.setattr(ExerciseService, "delete_exercise", AsyncMock(return_value=False))
    assert client.delete("/workouts/exercises/missing").status_code == 404


def test_enum_endpoints(client):
    assert client.get("/workouts/enums/body-parts").status_code == 200
    assert client.get("/workouts/enums/advancements").status_code == 200
    assert client.get("/workouts/enums/categories").status_code == 200
    assert client.get("/workouts/enums/training-types").status_code == 200
    assert client.get("/workouts/enums/days").status_code == 200


def test_trainings_endpoints(client, monkeypatch):
    monkeypatch.setattr(TrainingService, "get_trainings", AsyncMock(return_value=[_training_dict()]))
    assert client.get("/workouts/trainings").status_code == 200

    monkeypatch.setattr(TrainingService, "get_training", AsyncMock(return_value=_training_dict()))
    assert client.get("/workouts/trainings/tr-1").status_code == 200

    monkeypatch.setattr(TrainingService, "get_training", AsyncMock(return_value=None))
    assert client.get("/workouts/trainings/missing").status_code == 404

    monkeypatch.setattr(
        TrainingService,
        "get_training_with_exercises",
        AsyncMock(return_value={**_training_dict(), "exercises": []}),
    )
    assert client.get("/workouts/trainings/tr-1/with-exercises").status_code == 200

    monkeypatch.setattr(TrainingService, "create_training", AsyncMock(return_value=_training_dict("tr-2")))
    create_ok = client.post(
        "/workouts/trainings",
        headers={"x-user-id": "trainer-1"},
        json={
            "name": "Push",
            "training_type": "push",
            "est_time": 1800,
            "exercises": [{"exercise_id": "ex-1", "sets": [{"volume": 10, "units": "reps"}]}],
        },
    )
    assert create_ok.status_code == 201

    monkeypatch.setattr(TrainingService, "create_training", AsyncMock(side_effect=ValueError("invalid")))
    create_bad = client.post(
        "/workouts/trainings",
        headers={"x-user-id": "trainer-1"},
        json={
            "name": "Push",
            "training_type": "push",
            "est_time": 1800,
            "exercises": [{"exercise_id": "bad", "sets": [{"volume": 10, "units": "reps"}]}],
        },
    )
    assert create_bad.status_code == 400


def test_update_and_delete_training(client, monkeypatch):
    monkeypatch.setattr(TrainingService, "update_training", AsyncMock(return_value=_training_dict()))
    assert client.put("/workouts/trainings/tr-1", json={"name": "Updated"}).status_code == 200

    monkeypatch.setattr(TrainingService, "update_training", AsyncMock(return_value=None))
    assert client.put("/workouts/trainings/missing", json={"name": "Updated"}).status_code == 500

    monkeypatch.setattr(TrainingService, "delete_training", AsyncMock(return_value=True))
    assert client.delete("/workouts/trainings/tr-1").status_code == 204

    monkeypatch.setattr(TrainingService, "delete_training", AsyncMock(return_value=False))
    assert client.delete("/workouts/trainings/missing").status_code == 404


def test_plan_endpoints(client, monkeypatch):
    monkeypatch.setattr(WorkoutPlanService, "get_workout_plans", AsyncMock(return_value=[_plan_dict()]))
    assert client.get("/workouts/plans").status_code == 200

    monkeypatch.setattr(WorkoutPlanService, "get_trainer_plans", AsyncMock(return_value=[_plan_dict()]))
    assert client.get("/workouts/plans/my-plans", headers={"x-user-id": "trainer-1"}).status_code == 200

    monkeypatch.setattr(WorkoutPlanService, "get_client_plans", AsyncMock(return_value=[_plan_dict()]))
    assert client.get("/workouts/plans/assigned-to-me", headers={"x-user-id": "client-1"}).status_code == 200

    monkeypatch.setattr(WorkoutPlanService, "get_workout_plan", AsyncMock(return_value=_plan_dict()))
    assert client.get("/workouts/plans/plan-1").status_code == 200

    monkeypatch.setattr(WorkoutPlanService, "get_workout_plan_detailed", AsyncMock(return_value={**_plan_dict(), "trainings": []}))
    assert client.get("/workouts/plans/plan-1/detailed").status_code == 200


def test_plan_mutations(client, monkeypatch):
    monkeypatch.setattr(WorkoutPlanService, "create_workout_plan", AsyncMock(return_value=_plan_dict("plan-2")))
    assert client.post("/workouts/plans", headers={"x-user-id": "trainer-1"}, json={"name": "Plan", "is_public": False}).status_code == 201

    monkeypatch.setattr(WorkoutPlanService, "update_workout_plan", AsyncMock(return_value=_plan_dict()))
    assert client.put("/workouts/plans/plan-1", headers={"x-user-id": "trainer-1"}, json={"name": "X"}).status_code == 200

    monkeypatch.setattr(WorkoutPlanService, "update_workout_plan", AsyncMock(side_effect=PermissionError("no")))
    assert client.put("/workouts/plans/plan-1", headers={"x-user-id": "trainer-1"}, json={"name": "X"}).status_code == 403

    monkeypatch.setattr(WorkoutPlanService, "delete_workout_plan", AsyncMock(return_value=True))
    assert client.delete("/workouts/plans/plan-1", headers={"x-user-id": "trainer-1"}).status_code == 204

    monkeypatch.setattr(WorkoutPlanService, "add_client_to_plan", AsyncMock(return_value=_plan_dict()))
    assert client.post("/workouts/plans/plan-1/clients/client-1", headers={"x-user-id": "trainer-1"}).status_code == 200

    monkeypatch.setattr(WorkoutPlanService, "remove_client_from_plan", AsyncMock(return_value=_plan_dict()))
    assert client.delete("/workouts/plans/plan-1/clients/client-1", headers={"x-user-id": "trainer-1"}).status_code == 200

    monkeypatch.setattr(WorkoutPlanService, "add_training_to_plan", AsyncMock(return_value={**_plan_dict(), "trainings": ["tr-1"]}))
    assert client.post("/workouts/plans/plan-1/trainings/tr-1", headers={"x-user-id": "trainer-1"}).status_code == 200

    monkeypatch.setattr(WorkoutPlanService, "remove_training_from_plan", AsyncMock(return_value=_plan_dict()))
    assert client.delete("/workouts/plans/plan-1/trainings/tr-1", headers={"x-user-id": "trainer-1"}).status_code == 200

    monkeypatch.setattr(WorkoutPlanService, "like_workout_plan", AsyncMock(return_value={**_plan_dict(), "total_likes": 1}))
    assert client.post("/workouts/plans/plan-1/like").status_code == 200

    monkeypatch.setattr(WorkoutPlanService, "unlike_workout_plan", AsyncMock(return_value=_plan_dict()))
    assert client.post("/workouts/plans/plan-1/unlike").status_code == 200
