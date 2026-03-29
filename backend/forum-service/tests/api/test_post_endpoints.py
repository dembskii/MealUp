from unittest.mock import ANY, AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from src.api import posts as post_routes
from tests.factories import DEFAULT_USER_ID, OTHER_USER_ID, build_post


def _post_create_payload() -> dict:
    return {
        "title": "High-protein lunch",
        "content": "Chicken, rice and veggies is a reliable option after training.",
        "tags": ["nutrition", "mealprep"],
        "images": ["https://example.com/lunch.jpg"],
        "linked_recipes": [str(uuid4())],
        "linked_workouts": [str(uuid4())],
    }


def test_get_user_id_from_header_returns_header_value():
    assert post_routes.get_user_id_from_header(DEFAULT_USER_ID) == DEFAULT_USER_ID


def test_get_required_user_id_prefers_header_value():
    result = post_routes.get_required_user_id(
        x_user_id=DEFAULT_USER_ID,
        token_payload={"internal_uid": OTHER_USER_ID, "sub": OTHER_USER_ID},
    )

    assert result == DEFAULT_USER_ID


def test_get_required_user_id_falls_back_to_token_payload():
    result = post_routes.get_required_user_id(
        x_user_id=None,
        token_payload={"internal_uid": DEFAULT_USER_ID},
    )

    assert result == DEFAULT_USER_ID


def test_get_required_user_id_raises_401_when_no_user_id_available():
    with pytest.raises(HTTPException) as exc_info:
        post_routes.get_required_user_id(x_user_id=None, token_payload={})

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "User ID not found in header or token"


@patch("src.api.posts.PostService.get_all_posts", new_callable=AsyncMock)
def test_get_all_posts_success(mock_get_all_posts, client):
    post = build_post()
    mock_get_all_posts.return_value = [post]

    response = client.get("/forum/posts", params={"skip": 2, "limit": 5})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["_id"] == str(post.id)
    assert body[0]["author_id"] == str(post.author_id)
    mock_get_all_posts.assert_awaited_once_with(ANY, 2, 5)


@patch("src.api.posts.PostService.get_trending_posts", new_callable=AsyncMock)
def test_get_trending_posts_success(mock_get_trending_posts, client):
    post = build_post()
    mock_get_trending_posts.return_value = [post]

    response = client.get(
        "/forum/posts/trending",
        params={"skip": 1, "limit": 10, "min_coefficient": 0.5},
    )

    assert response.status_code == 200
    assert response.json()[0]["_id"] == str(post.id)
    mock_get_trending_posts.assert_awaited_once_with(ANY, 1, 10, 0.5)


@patch("src.api.posts.PostService.get_post_by_id", new_callable=AsyncMock)
def test_get_post_by_id_success(mock_get_post_by_id, client):
    post = build_post()
    mock_get_post_by_id.return_value = post

    response = client.get(f"/forum/posts/{post.id}")

    assert response.status_code == 200
    assert response.json()["_id"] == str(post.id)
    mock_get_post_by_id.assert_awaited_once_with(ANY, post.id)


@patch("src.api.posts.PostService.get_post_by_id", new_callable=AsyncMock)
def test_get_post_by_id_not_found(mock_get_post_by_id, client):
    mock_get_post_by_id.return_value = None

    response = client.get(f"/forum/posts/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Post not found"


@patch("src.api.posts.PostService.create_post", new_callable=AsyncMock)
def test_create_post_success(mock_create_post, client):
    created_post = build_post(author_id=DEFAULT_USER_ID)
    mock_create_post.return_value = created_post

    response = client.post(
        "/forum/posts",
        json=_post_create_payload(),
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 201
    assert response.json()["_id"] == str(created_post.id)
    called_session, called_payload = mock_create_post.await_args.args
    assert called_session is not None
    assert isinstance(called_payload["author_id"], UUID)
    assert str(called_payload["author_id"]) == DEFAULT_USER_ID


@patch("src.api.posts.PostService.create_post", new_callable=AsyncMock)
def test_create_post_returns_400_for_invalid_user_id(mock_create_post, client):
    response = client.post(
        "/forum/posts",
        json=_post_create_payload(),
        headers={"X-User-Id": "not-a-uuid"},
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Invalid User ID format")
    mock_create_post.assert_not_awaited()


@patch("src.api.posts.PostService.create_post", new_callable=AsyncMock)
def test_create_post_returns_500_when_service_fails(mock_create_post, client):
    mock_create_post.return_value = None

    response = client.post(
        "/forum/posts",
        json=_post_create_payload(),
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to create post"


@patch("src.api.posts.PostService.update_post", new_callable=AsyncMock)
@patch("src.api.posts.PostService.get_post_by_id", new_callable=AsyncMock)
def test_update_post_success(mock_get_post_by_id, mock_update_post, client):
    existing_post = build_post(author_id=DEFAULT_USER_ID)
    updated_post = build_post(
        post_id=existing_post.id,
        author_id=DEFAULT_USER_ID,
        title="Updated title",
    )
    mock_get_post_by_id.return_value = existing_post
    mock_update_post.return_value = updated_post

    response = client.put(
        f"/forum/posts/{existing_post.id}",
        json={"title": "Updated title"},
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated title"
    mock_update_post.assert_awaited_once_with(ANY, existing_post.id, {"title": "Updated title"})


@patch("src.api.posts.PostService.update_post", new_callable=AsyncMock)
@patch("src.api.posts.PostService.get_post_by_id", new_callable=AsyncMock)
def test_update_post_returns_404_when_post_missing(mock_get_post_by_id, mock_update_post, client):
    mock_get_post_by_id.return_value = None

    response = client.put(
        f"/forum/posts/{uuid4()}",
        json={"title": "Updated title"},
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Post not found"
    mock_update_post.assert_not_awaited()


@patch("src.api.posts.PostService.update_post", new_callable=AsyncMock)
@patch("src.api.posts.PostService.get_post_by_id", new_callable=AsyncMock)
def test_update_post_returns_403_for_non_author(mock_get_post_by_id, mock_update_post, client):
    existing_post = build_post(author_id=OTHER_USER_ID)
    mock_get_post_by_id.return_value = existing_post

    response = client.put(
        f"/forum/posts/{existing_post.id}",
        json={"title": "Updated title"},
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to update this post"
    mock_update_post.assert_not_awaited()


@patch("src.api.posts.PostService.update_post", new_callable=AsyncMock)
@patch("src.api.posts.PostService.get_post_by_id", new_callable=AsyncMock)
def test_update_post_returns_500_on_service_failure(mock_get_post_by_id, mock_update_post, client):
    existing_post = build_post(author_id=DEFAULT_USER_ID)
    mock_get_post_by_id.return_value = existing_post
    mock_update_post.return_value = None

    response = client.put(
        f"/forum/posts/{existing_post.id}",
        json={"title": "Updated title"},
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to update post"


@patch("src.api.posts.PostService.delete_post", new_callable=AsyncMock)
@patch("src.api.posts.PostService.get_post_by_id", new_callable=AsyncMock)
def test_delete_post_success_with_internal_uid(mock_get_post_by_id, mock_delete_post, client):
    existing_post = build_post(author_id=DEFAULT_USER_ID)
    mock_get_post_by_id.return_value = existing_post
    mock_delete_post.return_value = True

    response = client.delete(f"/forum/posts/{existing_post.id}")

    assert response.status_code == 204
    mock_delete_post.assert_awaited_once_with(ANY, existing_post.id)


@patch("src.api.posts.PostService.delete_post", new_callable=AsyncMock)
@patch("src.api.posts.PostService.get_post_by_id", new_callable=AsyncMock)
def test_delete_post_returns_404_when_post_missing(mock_get_post_by_id, mock_delete_post, client):
    mock_get_post_by_id.return_value = None

    response = client.delete(f"/forum/posts/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Post not found"
    mock_delete_post.assert_not_awaited()


@patch("src.api.posts.PostService.delete_post", new_callable=AsyncMock)
@patch("src.api.posts.PostService.get_post_by_id", new_callable=AsyncMock)
def test_delete_post_returns_403_for_non_author(mock_get_post_by_id, mock_delete_post, client):
    existing_post = build_post(author_id=OTHER_USER_ID)
    mock_get_post_by_id.return_value = existing_post

    response = client.delete(
        f"/forum/posts/{existing_post.id}",
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to delete this post"
    mock_delete_post.assert_not_awaited()


@patch("src.api.posts.PostService.delete_post", new_callable=AsyncMock)
@patch("src.api.posts.PostService.get_post_by_id", new_callable=AsyncMock)
def test_delete_post_returns_500_when_delete_fails(mock_get_post_by_id, mock_delete_post, client):
    existing_post = build_post(author_id=DEFAULT_USER_ID)
    mock_get_post_by_id.return_value = existing_post
    mock_delete_post.return_value = False

    response = client.delete(
        f"/forum/posts/{existing_post.id}",
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to delete post"


@patch("src.api.posts.PostService.track_post_view", new_callable=AsyncMock)
def test_track_post_view_success(mock_track_post_view, client):
    post_id = uuid4()
    mock_track_post_view.return_value = True

    response = client.post(
        f"/forum/posts/{post_id}/view",
        params={"engagement_seconds": 25},
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "View tracked successfully"}
    mock_track_post_view.assert_awaited_once_with(ANY, post_id, UUID(DEFAULT_USER_ID), 25)


@patch("src.api.posts.PostService.track_post_view", new_callable=AsyncMock)
def test_track_post_view_handles_invalid_optional_user_header(mock_track_post_view, client):
    post_id = uuid4()
    mock_track_post_view.return_value = True

    response = client.post(
        f"/forum/posts/{post_id}/view",
        headers={"X-User-Id": "invalid-user"},
    )

    assert response.status_code == 200
    mock_track_post_view.assert_awaited_once_with(ANY, post_id, None, None)


@patch("src.api.posts.PostService.track_post_view", new_callable=AsyncMock)
def test_track_post_view_returns_404_when_post_missing(mock_track_post_view, client):
    mock_track_post_view.return_value = False

    response = client.post(f"/forum/posts/{uuid4()}/view")

    assert response.status_code == 404
    assert response.json()["detail"] == "Post not found"


@patch("src.api.posts.PostService.get_post_views_count", new_callable=AsyncMock)
def test_get_post_views_success(mock_get_post_views_count, client):
    post_id = uuid4()
    mock_get_post_views_count.return_value = 12

    response = client.get(f"/forum/posts/{post_id}/views", params={"hours": 24})

    assert response.status_code == 200
    assert response.json() == {
        "post_id": str(post_id),
        "views_count": 12,
        "timeframe_hours": 24,
    }


@patch("src.api.posts.PostService.get_post_views_count", new_callable=AsyncMock)
def test_get_post_views_returns_404_when_post_missing(mock_get_post_views_count, client):
    mock_get_post_views_count.return_value = None

    response = client.get(f"/forum/posts/{uuid4()}/views")

    assert response.status_code == 404
    assert response.json()["detail"] == "Post not found"


@patch("src.api.posts.PostService.calculate_trending_coefficient", new_callable=AsyncMock)
def test_calculate_trending_coefficient_success(mock_calculate_trending, client):
    post_id = uuid4()
    mock_calculate_trending.return_value = 2.15

    response = client.post(f"/forum/posts/{post_id}/calculate-trending")

    assert response.status_code == 200
    assert response.json() == {
        "post_id": str(post_id),
        "trending_coefficient": 2.15,
    }


@patch("src.api.posts.PostService.calculate_trending_coefficient", new_callable=AsyncMock)
def test_calculate_trending_coefficient_returns_404_when_post_missing(mock_calculate_trending, client):
    mock_calculate_trending.return_value = None

    response = client.post(f"/forum/posts/{uuid4()}/calculate-trending")

    assert response.status_code == 404
    assert response.json()["detail"] == "Post not found"


@patch("src.api.posts.PostService.recalculate_all_trending_coefficients", new_callable=AsyncMock)
def test_recalculate_all_trending_success(mock_recalculate, client):
    mock_recalculate.return_value = 7

    response = client.post("/forum/posts/recalculate-trending")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Trending coefficients recalculated",
        "updated_posts": 7,
    }


@patch("src.api.posts.LikeService.track_post_like", new_callable=AsyncMock)
def test_like_post_success(mock_track_post_like, client):
    post_id = uuid4()
    mock_track_post_like.return_value = True

    response = client.post(
        f"/forum/posts/{post_id}/like",
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Post liked successfully"}
    mock_track_post_like.assert_awaited_once_with(ANY, post_id, UUID(DEFAULT_USER_ID))


@patch("src.api.posts.LikeService.track_post_like", new_callable=AsyncMock)
def test_like_post_returns_400_for_invalid_user_id(mock_track_post_like, client):
    response = client.post(
        f"/forum/posts/{uuid4()}/like",
        headers={"X-User-Id": "invalid-user"},
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Invalid User ID format")
    mock_track_post_like.assert_not_awaited()


@patch("src.api.posts.LikeService.track_post_like", new_callable=AsyncMock)
def test_like_post_returns_404_when_like_not_possible(mock_track_post_like, client):
    mock_track_post_like.return_value = False

    response = client.post(
        f"/forum/posts/{uuid4()}/like",
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Post not found or already liked"


@patch("src.api.posts.LikeService.track_post_unlike", new_callable=AsyncMock)
def test_unlike_post_success(mock_track_post_unlike, client):
    post_id = uuid4()
    mock_track_post_unlike.return_value = True

    response = client.delete(
        f"/forum/posts/{post_id}/like",
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Post unliked successfully"}
    mock_track_post_unlike.assert_awaited_once_with(ANY, post_id, UUID(DEFAULT_USER_ID))


@patch("src.api.posts.LikeService.track_post_unlike", new_callable=AsyncMock)
def test_unlike_post_returns_400_for_invalid_user_id(mock_track_post_unlike, client):
    response = client.delete(
        f"/forum/posts/{uuid4()}/like",
        headers={"X-User-Id": "invalid-user"},
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Invalid User ID format")
    mock_track_post_unlike.assert_not_awaited()


@patch("src.api.posts.LikeService.track_post_unlike", new_callable=AsyncMock)
def test_unlike_post_returns_404_when_unlike_not_possible(mock_track_post_unlike, client):
    mock_track_post_unlike.return_value = False

    response = client.delete(
        f"/forum/posts/{uuid4()}/like",
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Post not found or not liked"


@patch("src.api.posts.LikeService.get_post_likes_count", new_callable=AsyncMock)
def test_get_post_likes_success(mock_get_post_likes_count, client):
    post_id = uuid4()
    mock_get_post_likes_count.return_value = 14

    response = client.get(f"/forum/posts/{post_id}/likes")

    assert response.status_code == 200
    assert response.json() == {"post_id": str(post_id), "likes_count": 14}


@patch("src.api.posts.LikeService.get_post_likes_count", new_callable=AsyncMock)
def test_get_post_likes_returns_404_when_post_missing(mock_get_post_likes_count, client):
    mock_get_post_likes_count.return_value = None

    response = client.get(f"/forum/posts/{uuid4()}/likes")

    assert response.status_code == 404
    assert response.json()["detail"] == "Post not found"


@patch("src.api.posts.LikeService.has_user_liked_post", new_callable=AsyncMock)
def test_get_post_like_status_success(mock_has_user_liked_post, client):
    post_id = uuid4()
    mock_has_user_liked_post.return_value = True

    response = client.get(
        f"/forum/posts/{post_id}/like/status",
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 200
    assert response.json() == {"post_id": str(post_id), "liked": True}
    mock_has_user_liked_post.assert_awaited_once_with(ANY, post_id, UUID(DEFAULT_USER_ID))


@patch("src.api.posts.LikeService.has_user_liked_post", new_callable=AsyncMock)
def test_get_post_like_status_returns_400_for_invalid_user_id(mock_has_user_liked_post, client):
    response = client.get(
        f"/forum/posts/{uuid4()}/like/status",
        headers={"X-User-Id": "invalid-user"},
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Invalid User ID format")
    mock_has_user_liked_post.assert_not_awaited()


@patch("src.api.posts.LikeService.check_user_liked_posts", new_callable=AsyncMock)
def test_check_posts_liked_success(mock_check_user_liked_posts, client):
    first_post_id = uuid4()
    second_post_id = uuid4()
    mock_check_user_liked_posts.return_value = [str(first_post_id)]

    response = client.post(
        "/forum/posts/likes/check",
        json={"post_ids": [str(first_post_id), str(second_post_id)]},
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 200
    assert response.json() == {"liked_post_ids": [str(first_post_id)]}

    called_session, called_post_ids, called_user_id = mock_check_user_liked_posts.await_args.args
    assert called_session is not None
    assert called_post_ids == [first_post_id, second_post_id]
    assert called_user_id == UUID(DEFAULT_USER_ID)


@patch("src.api.posts.LikeService.check_user_liked_posts", new_callable=AsyncMock)
def test_check_posts_liked_returns_400_for_invalid_uuid_payload(mock_check_user_liked_posts, client):
    response = client.post(
        "/forum/posts/likes/check",
        json={"post_ids": ["bad-uuid"]},
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Invalid UUID format")
    mock_check_user_liked_posts.assert_not_awaited()
