from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

import src.api.routes as routes
from src.models.model import LikedRecipe, LikedWorkout, User
from src.validators.schema import (
    BulkLikeCheckRequest,
    BulkRecipeLikeCheckRequest,
    LikeRecipeRequest,
    LikeWorkoutRequest,
    UserCreate,
    UserUpdate,
)


class _ExecResult:
    def __init__(self, first_value=None):
        self._first_value = first_value

    def first(self):
        return self._first_value


def _user() -> User:
    return User(
        uid=uuid4(),
        auth0_sub="auth0|u1",
        email="john@example.com",
        username="johnny",
        first_name="John",
        last_name="Doe",
    )


@pytest.mark.asyncio
async def test_get_users_routes(monkeypatch: pytest.MonkeyPatch):
    user = _user()
    monkeypatch.setattr(routes.UserService, "get_all_users", AsyncMock(return_value=[user]))

    ok = await routes.get_all_users(session=AsyncMock(), token_payload={"sub": "u1"})
    assert ok.total == 1

    monkeypatch.setattr(routes.UserService, "get_all_users", AsyncMock(side_effect=RuntimeError("boom")))
    with pytest.raises(HTTPException) as exc:
        await routes.get_all_users(session=AsyncMock(), token_payload={"sub": "u1"})
    assert exc.value.status_code == 500


@pytest.mark.asyncio
async def test_get_user_routes(monkeypatch: pytest.MonkeyPatch):
    uid = uuid4()
    user = _user()

    monkeypatch.setattr(routes.UserService, "get_user_by_uid", AsyncMock(return_value=user))
    assert await routes.get_user(uid, session=AsyncMock(), token_payload={"sub": "u1"}) == user

    monkeypatch.setattr(routes.UserService, "get_user_by_uid", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as not_found:
        await routes.get_user(uid, session=AsyncMock(), token_payload={"sub": "u1"})
    assert not_found.value.status_code == 404

    monkeypatch.setattr(routes.UserService, "get_user_by_uid", AsyncMock(side_effect=RuntimeError("x")))
    with pytest.raises(HTTPException) as server_err:
        await routes.get_user(uid, session=AsyncMock(), token_payload={"sub": "u1"})
    assert server_err.value.status_code == 500


@pytest.mark.asyncio
async def test_get_user_by_auth0_routes(monkeypatch: pytest.MonkeyPatch):
    user = _user()
    monkeypatch.setattr(routes.UserService, "get_user_by_auth0_sub", AsyncMock(return_value=user))
    assert await routes.get_user_by_auth0("auth0|u1", session=AsyncMock(), token_payload={"sub": "u1"}) == user

    monkeypatch.setattr(routes.UserService, "get_user_by_auth0_sub", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as not_found:
        await routes.get_user_by_auth0("auth0|u1", session=AsyncMock(), token_payload={"sub": "u1"})
    assert not_found.value.status_code == 404


@pytest.mark.asyncio
async def test_create_update_delete_and_search_user_routes(monkeypatch: pytest.MonkeyPatch):
    uid = uuid4()
    session = AsyncMock()
    session.add = MagicMock()

    payload = UserCreate(
        email="john@example.com",
        username="johnny",
        first_name="John",
        last_name="Doe",
    )
    created = await routes.create_user(payload, session=session, token_payload={"sub": "u1"})
    assert created.email == "john@example.com"
    session.commit.assert_awaited_once()

    bad_session = AsyncMock()
    bad_session.add = MagicMock()
    bad_session.commit = AsyncMock(side_effect=RuntimeError("db"))
    with pytest.raises(HTTPException) as create_err:
        await routes.create_user(payload, session=bad_session, token_payload={"sub": "u1"})
    assert create_err.value.status_code == 500
    bad_session.rollback.assert_awaited_once()

    user = _user()
    monkeypatch.setattr(routes.UserService, "update_user", AsyncMock(return_value=user))
    updated = await routes.update_user(
        uid,
        UserUpdate(first_name="Jane"),
        session=AsyncMock(),
        token_payload={"sub": "u1"},
    )
    assert updated == user

    monkeypatch.setattr(routes.UserService, "update_user", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as update_not_found:
        await routes.update_user(uid, UserUpdate(first_name="Jane"), session=AsyncMock(), token_payload={"sub": "u1"})
    assert update_not_found.value.status_code == 404

    monkeypatch.setattr(routes.UserService, "delete_user", AsyncMock(return_value=True))
    deleted = await routes.delete_user(uid, session=AsyncMock(), token_payload={"sub": "u1"})
    assert deleted["message"] == "User deleted successfully"

    monkeypatch.setattr(routes.UserService, "delete_user", AsyncMock(return_value=False))
    with pytest.raises(HTTPException) as delete_not_found:
        await routes.delete_user(uid, session=AsyncMock(), token_payload={"sub": "u1"})
    assert delete_not_found.value.status_code == 404

    monkeypatch.setattr(routes.UserService, "search_users", AsyncMock(return_value=[user]))
    search_res = await routes.search_users("john", session=AsyncMock(), token_payload={"sub": "u1"})
    assert search_res.total == 1


@pytest.mark.asyncio
async def test_sync_user_from_auth_routes(monkeypatch: pytest.MonkeyPatch):
    user = _user()
    session = AsyncMock()

    with pytest.raises(HTTPException) as missing_sub:
        await routes.sync_user_from_auth({"email": "x@example.com"}, session=session)
    assert missing_sub.value.status_code == 400

    monkeypatch.setattr(routes.UserService, "get_or_create_user", AsyncMock(return_value=user))
    synced = await routes.sync_user_from_auth({"sub": "auth0|u1", "email": "john@example.com"}, session=session)
    assert synced == user

    monkeypatch.setattr(routes.UserService, "get_or_create_user", AsyncMock(side_effect=RuntimeError("sync fail")))
    with pytest.raises(HTTPException) as sync_err:
        await routes.sync_user_from_auth({"sub": "auth0|u1"}, session=session)
    assert sync_err.value.status_code == 500


@pytest.mark.asyncio
async def test_workout_like_routes(monkeypatch: pytest.MonkeyPatch):
    uid = uuid4()
    session = AsyncMock()
    workout = LikedWorkout(id=uuid4(), user_id=uid, workout_id="w1", created_at=datetime.now(timezone.utc))

    monkeypatch.setattr(routes.UserService, "like_workout", AsyncMock(return_value=True))
    monkeypatch.setattr(routes.UserService, "search_liked_workouts", AsyncMock(return_value=[workout]))
    liked = await routes.like_workout(
        uid,
        LikeWorkoutRequest(workout_id="w1"),
        session=session,
        token_payload={"sub": "u1"},
    )
    assert liked.workout_id == "w1"

    monkeypatch.setattr(routes.UserService, "like_workout", AsyncMock(return_value=False))
    with pytest.raises(HTTPException) as already_liked:
        await routes.like_workout(uid, LikeWorkoutRequest(workout_id="w1"), session=session, token_payload={"sub": "u1"})
    assert already_liked.value.status_code == 409

    monkeypatch.setattr(routes.UserService, "like_workout", AsyncMock(return_value=True))
    monkeypatch.setattr(routes.UserService, "search_liked_workouts", AsyncMock(return_value=[]))
    with pytest.raises(HTTPException) as fetch_fail:
        await routes.like_workout(uid, LikeWorkoutRequest(workout_id="w1"), session=session, token_payload={"sub": "u1"})
    assert fetch_fail.value.status_code == 500

    monkeypatch.setattr(routes.UserService, "unlike_workout", AsyncMock(return_value=True))
    unliked = await routes.unlike_workout(uid, "w1", session=session, token_payload={"sub": "u1"})
    assert unliked["message"] == "Workout unliked successfully"

    monkeypatch.setattr(routes.UserService, "unlike_workout", AsyncMock(return_value=False))
    with pytest.raises(HTTPException) as unlike_missing:
        await routes.unlike_workout(uid, "w1", session=session, token_payload={"sub": "u1"})
    assert unlike_missing.value.status_code == 404

    monkeypatch.setattr(routes.UserService, "is_workout_liked", AsyncMock(return_value=True))
    check = await routes.check_workout_liked(uid, "w1", session=session, token_payload={"sub": "u1"})
    assert check.is_liked is True

    monkeypatch.setattr(routes.UserService, "is_workout_liked", AsyncMock(side_effect=RuntimeError("x")))
    with pytest.raises(HTTPException) as check_err:
        await routes.check_workout_liked(uid, "w1", session=session, token_payload={"sub": "u1"})
    assert check_err.value.status_code == 500


@pytest.mark.asyncio
async def test_workout_bulk_and_list_routes(monkeypatch: pytest.MonkeyPatch):
    uid = uuid4()
    session = AsyncMock()
    workout = LikedWorkout(id=uuid4(), user_id=uid, workout_id="w1", created_at=datetime.now(timezone.utc))

    monkeypatch.setattr(routes.UserService, "is_workout_liked", AsyncMock(side_effect=[True, False]))
    bulk = await routes.check_workouts_liked_bulk(
        uid,
        BulkLikeCheckRequest(workout_ids=["w1", "w2"]),
        session=session,
        token_payload={"sub": "u1"},
    )
    assert bulk.results == {"w1": True, "w2": False}

    monkeypatch.setattr(routes.UserService, "get_liked_workouts", AsyncMock(return_value=[workout]))
    monkeypatch.setattr(routes.UserService, "get_liked_workouts_count", AsyncMock(return_value=1))
    listed = await routes.get_liked_workouts(uid, session=session, token_payload={"sub": "u1"})
    assert listed.total == 1

    monkeypatch.setattr(routes.UserService, "search_liked_workouts", AsyncMock(return_value=[workout]))
    searched = await routes.search_liked_workouts(
        uid,
        workout_ids="w1, w2",
        session=session,
        token_payload={"sub": "u1"},
    )
    assert searched.total == 1

    monkeypatch.setattr(routes.UserService, "search_liked_workouts", AsyncMock(side_effect=RuntimeError("x")))
    with pytest.raises(HTTPException) as search_err:
        await routes.search_liked_workouts(uid, session=session, token_payload={"sub": "u1"})
    assert search_err.value.status_code == 500


@pytest.mark.asyncio
async def test_recipe_like_routes(monkeypatch: pytest.MonkeyPatch):
    uid = uuid4()
    session = AsyncMock()
    recipe = LikedRecipe(id=uuid4(), user_id=uid, recipe_id="r1", created_at=datetime.now(timezone.utc))

    monkeypatch.setattr(routes.UserService, "like_recipe", AsyncMock(return_value=True))
    session.exec = AsyncMock(return_value=_ExecResult(first_value=recipe))

    liked = await routes.like_recipe(
        uid,
        LikeRecipeRequest(recipe_id="r1"),
        session=session,
        token_payload={"sub": "u1"},
    )
    assert liked.recipe_id == "r1"

    monkeypatch.setattr(routes.UserService, "like_recipe", AsyncMock(return_value=False))
    with pytest.raises(HTTPException) as already_liked:
        await routes.like_recipe(uid, LikeRecipeRequest(recipe_id="r1"), session=session, token_payload={"sub": "u1"})
    assert already_liked.value.status_code == 409

    monkeypatch.setattr(routes.UserService, "like_recipe", AsyncMock(return_value=True))
    session.exec = AsyncMock(return_value=_ExecResult(first_value=None))
    with pytest.raises(HTTPException) as retrieve_fail:
        await routes.like_recipe(uid, LikeRecipeRequest(recipe_id="r1"), session=session, token_payload={"sub": "u1"})
    assert retrieve_fail.value.status_code == 500

    monkeypatch.setattr(routes.UserService, "unlike_recipe", AsyncMock(return_value=True))
    unliked = await routes.unlike_recipe(uid, "r1", session=session, token_payload={"sub": "u1"})
    assert unliked["message"] == "Recipe unliked successfully"

    monkeypatch.setattr(routes.UserService, "unlike_recipe", AsyncMock(return_value=False))
    with pytest.raises(HTTPException) as unlike_missing:
        await routes.unlike_recipe(uid, "r1", session=session, token_payload={"sub": "u1"})
    assert unlike_missing.value.status_code == 404


@pytest.mark.asyncio
async def test_recipe_bulk_and_list_routes(monkeypatch: pytest.MonkeyPatch):
    uid = uuid4()
    session = AsyncMock()
    recipe = LikedRecipe(id=uuid4(), user_id=uid, recipe_id="r1", created_at=datetime.now(timezone.utc))

    monkeypatch.setattr(routes.UserService, "is_recipe_liked", AsyncMock(side_effect=[True, False]))
    bulk = await routes.check_recipes_liked_bulk(
        uid,
        BulkRecipeLikeCheckRequest(recipe_ids=["r1", "r2"]),
        session=session,
        token_payload={"sub": "u1"},
    )
    assert bulk.results == {"r1": True, "r2": False}

    monkeypatch.setattr(routes.UserService, "get_liked_recipes", AsyncMock(return_value=[recipe]))
    monkeypatch.setattr(routes.UserService, "get_liked_recipes_count", AsyncMock(return_value=1))
    listed = await routes.get_liked_recipes(uid, session=session, token_payload={"sub": "u1"})
    assert listed.total == 1


@pytest.mark.asyncio
async def test_health_check_route():
    result = await routes.health_check()
    assert result["status"] == "healthy"
