import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

from src.services.comment_service import CommentService
from src.services.like_service import LikeService
from src.services import post_service as post_service_module
from src.services.post_service import PostService
from tests.unit.fakes import FakeAsyncSession, FakeResult


def run(coro):
    return asyncio.run(coro)


def _uid(value: str = "11111111-1111-1111-1111-111111111111") -> UUID:
    return UUID(value)


def _post(post_id=None, author_id=None):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=post_id or uuid4(),
        author_id=author_id or uuid4(),
        title="Post",
        content="Content",
        tags=["fit"],
        images=[],
        linked_recipes=[],
        linked_workouts=[],
        total_likes=0,
        views_count=0,
        trending_coefficient=0.0,
        created_at=now,
        updated_at=now,
    )


def _comment(comment_id=None, post_id=None, author_id=None, parent_comment_id=None):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=comment_id or uuid4(),
        post_id=post_id or uuid4(),
        author_id=author_id or uuid4(),
        content="Comment",
        parent_comment_id=parent_comment_id,
        total_likes=0,
        created_at=now,
        updated_at=now,
    )


# -------- CommentService --------

def test_create_comment_success():
    post = _post(post_id=uuid4())
    session = FakeAsyncSession(exec_plan=[FakeResult(first=post)])

    created = run(
        CommentService.create_comment(
            session=session,
            post_id=post.id,
            author_id=uuid4(),
            content="hello",
        )
    )

    assert created is not None
    assert created.content == "hello"
    assert session.commits == 1
    assert len(session.refreshed) == 1


def test_create_comment_returns_none_when_post_missing():
    session = FakeAsyncSession(exec_plan=[FakeResult(first=None)])

    created = run(
        CommentService.create_comment(
            session=session,
            post_id=uuid4(),
            author_id=uuid4(),
            content="hello",
        )
    )

    assert created is None


def test_create_comment_returns_none_when_parent_invalid():
    post = _post(post_id=uuid4())
    session = FakeAsyncSession(
        exec_plan=[
            FakeResult(first=post),
            FakeResult(first=None),
        ]
    )

    created = run(
        CommentService.create_comment(
            session=session,
            post_id=post.id,
            author_id=uuid4(),
            content="hello",
            parent_comment_id=uuid4(),
        )
    )

    assert created is None


def test_create_comment_returns_none_when_parent_from_other_post():
    post = _post(post_id=uuid4())
    parent = _comment(post_id=uuid4())
    session = FakeAsyncSession(
        exec_plan=[
            FakeResult(first=post),
            FakeResult(first=parent),
        ]
    )

    created = run(
        CommentService.create_comment(
            session=session,
            post_id=post.id,
            author_id=uuid4(),
            content="hello",
            parent_comment_id=parent.id,
        )
    )

    assert created is None


def test_create_comment_rolls_back_on_exception():
    session = FakeAsyncSession(exec_plan=[RuntimeError("db")])

    created = run(
        CommentService.create_comment(
            session=session,
            post_id=uuid4(),
            author_id=uuid4(),
            content="hello",
        )
    )

    assert created is None
    assert session.rollbacks == 1


def test_get_comment_by_id_found_and_error():
    comment = _comment()
    found_session = FakeAsyncSession(exec_plan=[FakeResult(first=comment)])
    error_session = FakeAsyncSession(exec_plan=[RuntimeError("db")])

    assert run(CommentService.get_comment_by_id(found_session, comment.id)) is comment
    assert run(CommentService.get_comment_by_id(error_session, comment.id)) is None


def test_get_comments_by_post_paths():
    post = _post(post_id=uuid4())
    comments = [_comment(post_id=post.id), _comment(post_id=post.id)]

    ok_session = FakeAsyncSession(
        exec_plan=[FakeResult(first=post), FakeResult(all_values=comments)]
    )
    missing_post_session = FakeAsyncSession(exec_plan=[FakeResult(first=None)])
    error_session = FakeAsyncSession(exec_plan=[RuntimeError("db")])

    assert len(run(CommentService.get_comments_by_post(ok_session, post.id))) == 2
    assert run(CommentService.get_comments_by_post(missing_post_session, post.id)) == []
    assert run(CommentService.get_comments_by_post(error_session, post.id)) == []


def test_get_comment_replies_paths():
    parent = uuid4()
    replies = [_comment(parent_comment_id=parent)]

    ok_session = FakeAsyncSession(exec_plan=[FakeResult(all_values=replies)])
    error_session = FakeAsyncSession(exec_plan=[RuntimeError("db")])

    assert len(run(CommentService.get_comment_replies(ok_session, parent))) == 1
    assert run(CommentService.get_comment_replies(error_session, parent)) == []


def test_get_comments_tree_builds_nested_structure_and_handles_error():
    post_id = uuid4()
    root = _comment(comment_id=uuid4(), post_id=post_id, parent_comment_id=None)
    child = _comment(comment_id=uuid4(), post_id=post_id, parent_comment_id=root.id)
    session = FakeAsyncSession(exec_plan=[FakeResult(all_values=[root, child])])

    tree = run(CommentService.get_comments_tree(session, post_id, max_depth=3))

    assert len(tree) == 1
    assert tree[0]["comment"].id == root.id
    assert tree[0]["replies"][0]["comment"].id == child.id

    error_session = FakeAsyncSession(exec_plan=[RuntimeError("db")])
    assert run(CommentService.get_comments_tree(error_session, post_id)) == []


def test_update_comment_paths():
    author_id = _uid()
    comment = _comment(author_id=author_id)

    success_session = FakeAsyncSession(exec_plan=[FakeResult(first=comment)])
    updated = run(CommentService.update_comment(success_session, comment.id, author_id, "new"))
    assert updated.content == "new"
    assert success_session.commits == 1

    missing_session = FakeAsyncSession(exec_plan=[FakeResult(first=None)])
    assert run(CommentService.update_comment(missing_session, uuid4(), author_id, "new")) is None

    wrong_author_session = FakeAsyncSession(exec_plan=[FakeResult(first=comment)])
    assert run(CommentService.update_comment(wrong_author_session, comment.id, uuid4(), "new")) is None

    error_session = FakeAsyncSession(exec_plan=[RuntimeError("db")])
    assert run(CommentService.update_comment(error_session, comment.id, author_id, "new")) is None
    assert error_session.rollbacks == 1


def test_delete_comment_paths(monkeypatch):
    author_id = _uid()
    comment = _comment(author_id=author_id)

    missing_session = FakeAsyncSession(exec_plan=[FakeResult(first=None)])
    assert run(CommentService.delete_comment(missing_session, uuid4(), author_id)) is False

    wrong_author_session = FakeAsyncSession(exec_plan=[FakeResult(first=comment)])
    assert run(CommentService.delete_comment(wrong_author_session, comment.id, uuid4())) is False

    recursive = AsyncMock()
    monkeypatch.setattr(CommentService, "_delete_comment_recursive", recursive)
    success_session = FakeAsyncSession(exec_plan=[FakeResult(first=comment)])
    assert run(CommentService.delete_comment(success_session, comment.id, author_id)) is True
    recursive.assert_awaited_once()

    failing_recursive = AsyncMock(side_effect=RuntimeError("boom"))
    monkeypatch.setattr(CommentService, "_delete_comment_recursive", failing_recursive)
    error_session = FakeAsyncSession(exec_plan=[FakeResult(first=comment)])
    assert run(CommentService.delete_comment(error_session, comment.id, author_id)) is False
    assert error_session.rollbacks == 1


def test_delete_comment_recursive_deletes_replies_likes_and_comment():
    root_id = uuid4()
    reply = _comment(comment_id=uuid4(), parent_comment_id=root_id)
    root = _comment(comment_id=root_id)

    session = FakeAsyncSession(
        exec_plan=[
            FakeResult(all_values=[reply]),
            FakeResult(all_values=[]),
            FakeResult(all_values=[SimpleNamespace(id=uuid4())]),
            FakeResult(first=reply),
            FakeResult(all_values=[SimpleNamespace(id=uuid4())]),
            FakeResult(first=root),
        ]
    )

    run(CommentService._delete_comment_recursive(session, root_id))

    assert len(session.deleted) == 4


def test_get_comments_count_by_post_paths():
    post_id = uuid4()
    ok = FakeAsyncSession(exec_plan=[FakeResult(first=5)])
    err = FakeAsyncSession(exec_plan=[RuntimeError("db")])

    assert run(CommentService.get_comments_count_by_post(ok, post_id)) == 5
    assert run(CommentService.get_comments_count_by_post(err, post_id)) == 0


# -------- LikeService --------

def test_track_post_like_paths():
    post = _post(post_id=uuid4())
    user_id = uuid4()

    already_liked = FakeAsyncSession(exec_plan=[FakeResult(first=SimpleNamespace())])
    assert run(LikeService.track_post_like(already_liked, post.id, user_id)) is False

    missing_post = FakeAsyncSession(exec_plan=[FakeResult(first=None), FakeResult(first=None)])
    assert run(LikeService.track_post_like(missing_post, post.id, user_id)) is False

    success = FakeAsyncSession(exec_plan=[FakeResult(first=None), FakeResult(first=post)])
    assert run(LikeService.track_post_like(success, post.id, user_id)) is True
    assert post.total_likes == 1

    failing = FakeAsyncSession(exec_plan=[RuntimeError("db")])
    assert run(LikeService.track_post_like(failing, post.id, user_id)) is False
    assert failing.rollbacks == 1


def test_track_post_unlike_paths():
    post = _post(post_id=uuid4())
    post.total_likes = 1
    user_id = uuid4()

    not_liked = FakeAsyncSession(exec_plan=[FakeResult(first=None)])
    assert run(LikeService.track_post_unlike(not_liked, post.id, user_id)) is False

    no_post = FakeAsyncSession(exec_plan=[FakeResult(first=SimpleNamespace()), FakeResult(first=None)])
    assert run(LikeService.track_post_unlike(no_post, post.id, user_id)) is False

    existing_like = SimpleNamespace(id=uuid4())
    success = FakeAsyncSession(exec_plan=[FakeResult(first=existing_like), FakeResult(first=post)])
    assert run(LikeService.track_post_unlike(success, post.id, user_id)) is True
    assert post.total_likes == 0

    failing = FakeAsyncSession(exec_plan=[RuntimeError("db")])
    assert run(LikeService.track_post_unlike(failing, post.id, user_id)) is False
    assert failing.rollbacks == 1


def test_get_post_likes_count_paths():
    post = _post(post_id=uuid4())

    missing = FakeAsyncSession(exec_plan=[FakeResult(first=None)])
    assert run(LikeService.get_post_likes_count(missing, post.id)) is None

    success = FakeAsyncSession(exec_plan=[FakeResult(first=post), FakeResult(first=3)])
    assert run(LikeService.get_post_likes_count(success, post.id)) == 3

    failing = FakeAsyncSession(exec_plan=[RuntimeError("db")])
    assert run(LikeService.get_post_likes_count(failing, post.id)) is None


def test_track_comment_like_paths():
    comment = _comment(comment_id=uuid4())
    user_id = uuid4()

    already = FakeAsyncSession(exec_plan=[FakeResult(first=SimpleNamespace())])
    assert run(LikeService.track_comment_like(already, comment.id, user_id)) is False

    missing = FakeAsyncSession(exec_plan=[FakeResult(first=None), FakeResult(first=None)])
    assert run(LikeService.track_comment_like(missing, comment.id, user_id)) is False

    success = FakeAsyncSession(exec_plan=[FakeResult(first=None), FakeResult(first=comment)])
    assert run(LikeService.track_comment_like(success, comment.id, user_id)) is True
    assert comment.total_likes == 1

    failing = FakeAsyncSession(exec_plan=[RuntimeError("db")])
    assert run(LikeService.track_comment_like(failing, comment.id, user_id)) is False
    assert failing.rollbacks == 1


def test_remove_comment_like_paths():
    comment = _comment(comment_id=uuid4())
    comment.total_likes = 1
    user_id = uuid4()

    not_liked = FakeAsyncSession(exec_plan=[FakeResult(first=None)])
    assert run(LikeService.remove_comment_like(not_liked, comment.id, user_id)) is False

    no_comment = FakeAsyncSession(exec_plan=[FakeResult(first=SimpleNamespace()), FakeResult(first=None)])
    assert run(LikeService.remove_comment_like(no_comment, comment.id, user_id)) is False

    existing_like = SimpleNamespace(id=uuid4())
    success = FakeAsyncSession(exec_plan=[FakeResult(first=existing_like), FakeResult(first=comment)])
    assert run(LikeService.remove_comment_like(success, comment.id, user_id)) is True
    assert comment.total_likes == 0

    failing = FakeAsyncSession(exec_plan=[RuntimeError("db")])
    assert run(LikeService.remove_comment_like(failing, comment.id, user_id)) is False
    assert failing.rollbacks == 1


def test_get_comment_likes_count_paths():
    comment = _comment(comment_id=uuid4())

    missing = FakeAsyncSession(exec_plan=[FakeResult(first=None)])
    assert run(LikeService.get_comment_likes_count(missing, comment.id)) is None

    success = FakeAsyncSession(exec_plan=[FakeResult(first=comment), FakeResult(first=4)])
    assert run(LikeService.get_comment_likes_count(success, comment.id)) == 4

    failing = FakeAsyncSession(exec_plan=[RuntimeError("db")])
    assert run(LikeService.get_comment_likes_count(failing, comment.id)) is None


def test_like_status_helpers():
    post_id = uuid4()
    comment_id = uuid4()
    user_id = uuid4()

    liked_post = FakeAsyncSession(exec_plan=[FakeResult(first=SimpleNamespace())])
    assert run(LikeService.has_user_liked_post(liked_post, post_id, user_id)) is True

    not_liked_post = FakeAsyncSession(exec_plan=[FakeResult(first=None)])
    assert run(LikeService.has_user_liked_post(not_liked_post, post_id, user_id)) is False

    liked_posts_list = FakeAsyncSession(exec_plan=[FakeResult(all_values=[post_id])])
    assert run(LikeService.check_user_liked_posts(liked_posts_list, [post_id], user_id)) == [str(post_id)]

    err_liked_posts = FakeAsyncSession(exec_plan=[RuntimeError("db")])
    assert run(LikeService.check_user_liked_posts(err_liked_posts, [post_id], user_id)) == []

    liked_comment = FakeAsyncSession(exec_plan=[FakeResult(first=SimpleNamespace())])
    assert run(LikeService.has_user_liked_comment(liked_comment, comment_id, user_id)) is True

    not_liked_comment = FakeAsyncSession(exec_plan=[FakeResult(first=None)])
    assert run(LikeService.has_user_liked_comment(not_liked_comment, comment_id, user_id)) is False

    liked_comments_list = FakeAsyncSession(exec_plan=[FakeResult(all_values=[comment_id])])
    assert run(LikeService.check_user_liked_comments(liked_comments_list, [comment_id], user_id)) == [str(comment_id)]

    err_liked_comments = FakeAsyncSession(exec_plan=[RuntimeError("db")])
    assert run(LikeService.check_user_liked_comments(err_liked_comments, [comment_id], user_id)) == []


# -------- PostService --------

def test_get_all_posts_and_get_post_by_id_paths():
    post = _post()

    all_ok = FakeAsyncSession(exec_plan=[FakeResult(all_values=[post])])
    assert run(PostService.get_all_posts(all_ok)) == [post]

    all_err = FakeAsyncSession(exec_plan=[RuntimeError("db")])
    assert run(PostService.get_all_posts(all_err)) == []

    by_id_ok = FakeAsyncSession(exec_plan=[FakeResult(first=post)])
    assert run(PostService.get_post_by_id(by_id_ok, post.id)) is post

    by_id_err = FakeAsyncSession(exec_plan=[RuntimeError("db")])
    assert run(PostService.get_post_by_id(by_id_err, post.id)) is None


def test_create_post_and_update_post_paths(monkeypatch):
    async def _embed(*args, **kwargs):
        return [0.1, 0.2]

    monkeypatch.setattr(post_service_module, "embed_post", _embed)

    author_id = uuid4()
    create_session = FakeAsyncSession()
    created = run(
        PostService.create_post(
            create_session,
            {
                "author_id": author_id,
                "title": "title",
                "content": "content",
            },
        )
    )
    assert created is not None
    assert create_session.commits >= 1

    fail_create_session = FakeAsyncSession(commit_plan=[RuntimeError("db")])
    assert (
        run(
            PostService.create_post(
                fail_create_session,
                {
                    "author_id": author_id,
                    "title": "title",
                    "content": "content",
                },
            )
        )
        is None
    )

    post = _post(post_id=uuid4(), author_id=author_id)
    post.views_count = 2

    update_session = FakeAsyncSession(exec_plan=[FakeResult(first=post)])
    updated = run(
        PostService.update_post(
            update_session,
            post.id,
            {
                "title": "new title",
                "author_id": uuid4(),
                "views_count": 999,
            },
        )
    )
    assert updated.title == "new title"
    assert updated.views_count == 2

    missing_update = FakeAsyncSession(exec_plan=[FakeResult(first=None)])
    assert run(PostService.update_post(missing_update, uuid4(), {"title": "x"})) is None

    err_update = FakeAsyncSession(exec_plan=[RuntimeError("db")])
    assert run(PostService.update_post(err_update, uuid4(), {"title": "x"})) is None


def test_delete_post_paths():
    post_id = uuid4()

    missing = FakeAsyncSession(exec_plan=[FakeResult(first=None)])
    assert run(PostService.delete_post(missing, post_id)) is False

    post = _post(post_id=post_id)
    success = FakeAsyncSession(
        exec_plan=[
            FakeResult(first=post),
            FakeResult(all_values=[uuid4(), uuid4()]),
            FakeResult(),
            FakeResult(),
            FakeResult(),
            FakeResult(),
            FakeResult(),
        ]
    )
    assert run(PostService.delete_post(success, post_id)) is True
    assert post in success.deleted

    failing = FakeAsyncSession(exec_plan=[RuntimeError("db")])
    assert run(PostService.delete_post(failing, post_id)) is False
    assert failing.rollbacks == 1


def test_track_post_view_paths():
    post = _post(post_id=uuid4())

    success = FakeAsyncSession(exec_plan=[FakeResult(first=post)])
    assert run(PostService.track_post_view(success, post.id, user_id=uuid4(), engagement_seconds=5)) is True
    assert post.views_count == 1
    assert success.commits == 2

    missing_post = FakeAsyncSession(exec_plan=[FakeResult(first=None)])
    assert run(PostService.track_post_view(missing_post, post.id)) is False

    failing = FakeAsyncSession(commit_plan=[RuntimeError("db")])
    assert run(PostService.track_post_view(failing, post.id)) is False
    assert failing.rollbacks == 1


def test_calculate_trending_and_related_helpers(monkeypatch):
    post = _post(post_id=uuid4())
    post.total_likes = 4
    post.views_count = 10
    post.created_at = datetime.now(timezone.utc) - timedelta(days=7)

    async def _comments_count(*args, **kwargs):
        return 2

    monkeypatch.setattr(post_service_module.CommentService, "get_comments_count_by_post", _comments_count)

    ok = FakeAsyncSession(exec_plan=[FakeResult(first=post)])
    coefficient = run(PostService.calculate_trending_coefficient(ok, post.id))
    assert coefficient is not None
    assert coefficient > 0

    not_found = FakeAsyncSession(exec_plan=[FakeResult(first=None)])
    assert run(PostService.calculate_trending_coefficient(not_found, post.id)) is None

    failing = FakeAsyncSession(exec_plan=[RuntimeError("db")])
    assert run(PostService.calculate_trending_coefficient(failing, post.id)) is None
    assert failing.rollbacks == 1

    trending_posts = FakeAsyncSession(exec_plan=[FakeResult(all_values=[post])])
    assert run(PostService.get_trending_posts(trending_posts)) == [post]

    trending_err = FakeAsyncSession(exec_plan=[RuntimeError("db")])
    assert run(PostService.get_trending_posts(trending_err)) == []


def test_get_post_views_count_and_recalculate(monkeypatch):
    post = _post(post_id=uuid4())

    missing = FakeAsyncSession(exec_plan=[FakeResult(first=None)])
    assert run(PostService.get_post_views_count(missing, post.id)) is None

    success = FakeAsyncSession(exec_plan=[FakeResult(first=post), FakeResult(first=12)])
    assert run(PostService.get_post_views_count(success, post.id, hours=24)) == 12

    failing = FakeAsyncSession(exec_plan=[RuntimeError("db")])
    assert run(PostService.get_post_views_count(failing, post.id)) is None

    async def _calc(session, pid):
        return 1.0 if str(pid).endswith("1") else None

    monkeypatch.setattr(PostService, "calculate_trending_coefficient", _calc)
    p1 = _post(post_id=UUID("00000000-0000-0000-0000-000000000001"))
    p2 = _post(post_id=UUID("00000000-0000-0000-0000-000000000002"))

    recalc_session = FakeAsyncSession(exec_plan=[FakeResult(all_values=[p1, p2])])
    assert run(PostService.recalculate_all_trending_coefficients(recalc_session)) == 1

    recalc_err = FakeAsyncSession(exec_plan=[RuntimeError("db")])
    assert run(PostService.recalculate_all_trending_coefficients(recalc_err)) == 0
