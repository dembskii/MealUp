from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.model import LikedRecipe, LikedWorkout, User, UserRole
from src.services.user_service import UserService


class _ExecResult:
    def __init__(self, first_value=None, all_values=None):
        self._first_value = first_value
        self._all_values = [] if all_values is None else all_values

    def first(self):
        return self._first_value

    def all(self):
        return self._all_values


def _user(auth0_sub: str = "auth0|abc", email: str = "john@example.com") -> User:
    return User(
        auth0_sub=auth0_sub,
        email=email,
        username="johnny",
        first_name="John",
        last_name="Doe",
    )


@pytest.mark.asyncio
async def test_get_or_create_user_updates_existing():
    existing = _user()
    session = AsyncMock()
    session.exec = AsyncMock(return_value=_ExecResult(first_value=existing))
    session.add = MagicMock()

    result = await UserService.get_or_create_user(
        session,
        "auth0|abc",
        {
            "email": "new@example.com",
            "given_name": "Jane",
            "family_name": "Smith",
        },
    )

    assert result is existing
    assert existing.email == "new@example.com"
    assert existing.first_name == "Jane"
    assert existing.last_name == "Smith"
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(existing)


@pytest.mark.asyncio
async def test_get_or_create_user_creates_new_with_invalid_role_default():
    session = AsyncMock()
    session.exec = AsyncMock(return_value=_ExecResult(first_value=None))
    session.add = MagicMock()

    result = await UserService.get_or_create_user(
        session,
        "auth0|new",
        {
            "email": "alice@example.com",
            "given_name": "Alice",
            "family_name": "Wonder",
            "role": "not-a-role",
        },
    )

    assert result.auth0_sub == "auth0|new"
    assert result.username == "alice"
    assert result.role == UserRole.USER
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_or_create_user_rollback_on_error():
    session = AsyncMock()
    session.exec = AsyncMock(side_effect=RuntimeError("db down"))

    with pytest.raises(RuntimeError):
        await UserService.get_or_create_user(session, "auth0|x", {"email": "x@example.com"})

    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_user_get_all_search_paths():
    user = _user()
    session = AsyncMock()
    session.exec = AsyncMock(
        side_effect=[
            _ExecResult(first_value=user),
            _ExecResult(first_value=user),
            _ExecResult(all_values=[user]),
            _ExecResult(all_values=[user]),
        ]
    )

    assert await UserService.get_user_by_auth0_sub(session, "auth0|abc") is user
    assert await UserService.get_user_by_uid(session, user.uid) is user

    all_users = await UserService.get_all_users(session, skip=0, limit=10)
    assert len(all_users) == 1

    searched = await UserService.search_users(session, "john")
    assert len(searched) == 1


@pytest.mark.asyncio
async def test_get_methods_return_empty_on_exception():
    session = AsyncMock()
    session.exec = AsyncMock(side_effect=RuntimeError("boom"))

    assert await UserService.get_user_by_auth0_sub(session, "x") is None
    assert await UserService.get_user_by_uid(session, uuid4()) is None
    assert await UserService.get_all_users(session) == []
    assert await UserService.search_users(session, "x") == []


@pytest.mark.asyncio
async def test_update_user_success_ignores_protected_fields():
    uid = uuid4()
    existing = _user()
    old_email = existing.email

    session = AsyncMock()
    session.exec = AsyncMock(return_value=_ExecResult(first_value=existing))
    session.add = MagicMock()

    updated = await UserService.update_user(
        session,
        uid,
        {
            "email": "blocked@example.com",
            "auth0_sub": "blocked",
            "username": "newname",
            "first_name": "Updated",
        },
    )

    assert updated is existing
    assert existing.username == "newname"
    assert existing.first_name == "Updated"
    assert existing.email == old_email
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_user_not_found_and_fetch_error():
    uid = uuid4()

    session_none = AsyncMock()
    session_none.exec = AsyncMock(return_value=_ExecResult(first_value=None))
    assert await UserService.update_user(session_none, uid, {"first_name": "X"}) is None

    session_error = AsyncMock()
    session_error.exec = AsyncMock(side_effect=RuntimeError("fetch failed"))
    with pytest.raises(RuntimeError):
        await UserService.update_user(session_error, uid, {"first_name": "X"})


@pytest.mark.asyncio
async def test_update_user_rollback_on_commit_error():
    uid = uuid4()
    existing = _user()
    session = AsyncMock()
    session.exec = AsyncMock(return_value=_ExecResult(first_value=existing))
    session.commit = AsyncMock(side_effect=RuntimeError("commit failed"))
    session.add = MagicMock()

    with pytest.raises(RuntimeError):
        await UserService.update_user(session, uid, {"first_name": "X"})

    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_user_paths():
    uid = uuid4()
    existing = _user()

    session = AsyncMock()
    session.exec = AsyncMock(side_effect=[_ExecResult(first_value=existing), _ExecResult(first_value=None)])

    assert await UserService.delete_user(session, uid) is True
    assert await UserService.delete_user(session, uid) is False

    session.delete.assert_awaited_once_with(existing)


@pytest.mark.asyncio
async def test_delete_user_on_error_rolls_back_and_returns_false():
    session = AsyncMock()
    session.exec = AsyncMock(side_effect=RuntimeError("db err"))

    assert await UserService.delete_user(session, uuid4()) is False
    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_workout_like_methods_paths():
    uid = uuid4()
    liked = LikedWorkout(user_id=uid, workout_id="w1", created_at=datetime.now(timezone.utc))

    session = AsyncMock()
    session.exec = AsyncMock(
        side_effect=[
            _ExecResult(first_value=liked),
            _ExecResult(first_value=None),
            _ExecResult(first_value=liked),
            _ExecResult(first_value=None),
            _ExecResult(first_value=liked),
            _ExecResult(all_values=[liked]),
            _ExecResult(first_value=3),
            _ExecResult(all_values=[liked]),
        ]
    )
    session.add = MagicMock()

    assert await UserService.like_workout(session, uid, "w1") is False
    assert await UserService.like_workout(session, uid, "w2") is True
    assert await UserService.unlike_workout(session, uid, "w1") is True
    assert await UserService.unlike_workout(session, uid, "w2") is False
    assert await UserService.is_workout_liked(session, uid, "w1") is True
    assert len(await UserService.get_liked_workouts(session, uid)) == 1
    assert await UserService.get_liked_workouts_count(session, uid) == 3
    assert len(await UserService.search_liked_workouts(session, uid, ["w1"])) == 1


@pytest.mark.asyncio
async def test_workout_like_methods_fail_safe_returns():
    session = AsyncMock()
    session.exec = AsyncMock(side_effect=RuntimeError("x"))

    assert await UserService.like_workout(session, uuid4(), "w") is False
    assert await UserService.unlike_workout(session, uuid4(), "w") is False
    assert await UserService.is_workout_liked(session, uuid4(), "w") is False
    assert await UserService.get_liked_workouts(session, uuid4()) == []
    assert await UserService.get_liked_workouts_count(session, uuid4()) == 0
    assert await UserService.search_liked_workouts(session, uuid4(), ["w"]) == []


@pytest.mark.asyncio
async def test_recipe_like_methods_paths():
    uid = uuid4()
    liked = LikedRecipe(user_id=uid, recipe_id="r1", created_at=datetime.now(timezone.utc))

    session = AsyncMock()
    session.exec = AsyncMock(
        side_effect=[
            _ExecResult(first_value=liked),
            _ExecResult(first_value=None),
            _ExecResult(first_value=liked),
            _ExecResult(first_value=None),
            _ExecResult(first_value=liked),
            _ExecResult(all_values=[liked]),
            _ExecResult(first_value=5),
        ]
    )
    session.add = MagicMock()

    assert await UserService.like_recipe(session, uid, "r1") is False
    assert await UserService.like_recipe(session, uid, "r2") is True
    assert await UserService.unlike_recipe(session, uid, "r1") is True
    assert await UserService.unlike_recipe(session, uid, "r2") is False
    assert await UserService.is_recipe_liked(session, uid, "r1") is True
    assert len(await UserService.get_liked_recipes(session, uid)) == 1
    assert await UserService.get_liked_recipes_count(session, uid) == 5


@pytest.mark.asyncio
async def test_recipe_like_methods_fail_safe_returns():
    session = AsyncMock()
    session.exec = AsyncMock(side_effect=RuntimeError("x"))

    assert await UserService.like_recipe(session, uuid4(), "r") is False
    assert await UserService.unlike_recipe(session, uuid4(), "r") is False
    assert await UserService.is_recipe_liked(session, uuid4(), "r") is False
    assert await UserService.get_liked_recipes(session, uuid4()) == []
    assert await UserService.get_liked_recipes_count(session, uuid4()) == 0
