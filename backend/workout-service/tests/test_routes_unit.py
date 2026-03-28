from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

import src.api.routes as routes


@pytest.mark.asyncio
async def test_header_guard():
    assert routes.get_user_id_from_header("u1") == "u1"
    with pytest.raises(HTTPException):
        routes.get_user_id_from_header(None)


@pytest.mark.asyncio
async def test_search_route_direct_success(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(routes.ExerciseService, "search_exercises", AsyncMock(return_value=[]))
    result = await routes.search_exercises(q="push")
    assert result == []


@pytest.mark.asyncio
async def test_search_route_direct_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(routes.ExerciseService, "search_exercises", AsyncMock(side_effect=RuntimeError("x")))
    with pytest.raises(HTTPException) as exc:
        await routes.search_exercises(q="push")
    assert exc.value.status_code == 500


@pytest.mark.asyncio
async def test_training_update_route_validation(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(routes.TrainingService, "update_training", AsyncMock(side_effect=ValueError("bad")))
    with pytest.raises(HTTPException) as exc:
        await routes.update_training("tr-1", routes.TrainingUpdate(name="X", est_time=1200, description=None))
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_plan_routes_error_branches(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(routes.WorkoutPlanService, "delete_workout_plan", AsyncMock(side_effect=PermissionError("no")))
    with pytest.raises(HTTPException) as exc1:
        await routes.delete_workout_plan("p1", "u1")
    assert exc1.value.status_code == 403

    monkeypatch.setattr(routes.WorkoutPlanService, "add_training_to_plan", AsyncMock(side_effect=ValueError("bad")))
    with pytest.raises(HTTPException) as exc2:
        await routes.add_training_to_plan("p1", "t1", "u1")
    assert exc2.value.status_code == 400


@pytest.mark.asyncio
async def test_routes_generic_error_branches(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(routes.TrainingService, "get_trainings", AsyncMock(side_effect=RuntimeError("x")))
    with pytest.raises(HTTPException) as exc1:
        await routes.get_trainings()
    assert exc1.value.status_code == 500

    monkeypatch.setattr(routes.WorkoutPlanService, "get_workout_plans", AsyncMock(side_effect=RuntimeError("x")))
    with pytest.raises(HTTPException) as exc2:
        await routes.get_workout_plans()
    assert exc2.value.status_code == 500

    monkeypatch.setattr(routes.WorkoutPlanService, "get_trainer_plans", AsyncMock(side_effect=RuntimeError("x")))
    with pytest.raises(HTTPException) as exc3:
        await routes.get_my_workout_plans("u1")
    assert exc3.value.status_code == 500

    monkeypatch.setattr(routes.WorkoutPlanService, "get_client_plans", AsyncMock(side_effect=RuntimeError("x")))
    with pytest.raises(HTTPException) as exc4:
        await routes.get_assigned_workout_plans("u1")
    assert exc4.value.status_code == 500


@pytest.mark.asyncio
async def test_routes_not_found_and_other_errors(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(routes.TrainingService, "get_training_with_exercises", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as exc1:
        await routes.get_training_with_exercises("tr-x")
    assert exc1.value.status_code == 404

    monkeypatch.setattr(routes.WorkoutPlanService, "get_workout_plan", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as exc2:
        await routes.get_workout_plan("p-x")
    assert exc2.value.status_code == 404

    monkeypatch.setattr(routes.WorkoutPlanService, "get_workout_plan_detailed", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as exc3:
        await routes.get_workout_plan_detailed("p-x")
    assert exc3.value.status_code == 404

    monkeypatch.setattr(routes.WorkoutPlanService, "create_workout_plan", AsyncMock(side_effect=RuntimeError("x")))
    with pytest.raises(HTTPException) as exc4:
        await routes.create_workout_plan(routes.WorkoutPlanCreate(name="p", description=None), "u1")
    assert exc4.value.status_code == 500


@pytest.mark.asyncio
async def test_routes_permission_and_not_found_mutations(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(routes.WorkoutPlanService, "update_workout_plan", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as exc1:
        await routes.update_workout_plan("p1", routes.WorkoutPlanUpdate(name="x", description=None), "u1")
    assert exc1.value.status_code == 500

    monkeypatch.setattr(routes.WorkoutPlanService, "delete_workout_plan", AsyncMock(return_value=False))
    with pytest.raises(HTTPException) as exc2:
        await routes.delete_workout_plan("p1", "u1")
    assert exc2.value.status_code == 500

    monkeypatch.setattr(routes.WorkoutPlanService, "add_client_to_plan", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as exc3:
        await routes.add_client_to_plan("p1", "c1", "u1")
    assert exc3.value.status_code == 500

    monkeypatch.setattr(routes.WorkoutPlanService, "remove_client_from_plan", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as exc4:
        await routes.remove_client_from_plan("p1", "c1", "u1")
    assert exc4.value.status_code == 500

    monkeypatch.setattr(routes.WorkoutPlanService, "remove_training_from_plan", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as exc5:
        await routes.remove_training_from_plan("p1", "t1", "u1")
    assert exc5.value.status_code == 500


@pytest.mark.asyncio
async def test_like_unlike_route_branches(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(routes.WorkoutPlanService, "like_workout_plan", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as exc1:
        await routes.like_workout_plan("p1")
    assert exc1.value.status_code == 500

    monkeypatch.setattr(routes.WorkoutPlanService, "unlike_workout_plan", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as exc2:
        await routes.unlike_workout_plan("p1")
    assert exc2.value.status_code == 500
