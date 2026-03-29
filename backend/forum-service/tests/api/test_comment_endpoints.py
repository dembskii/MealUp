from unittest.mock import ANY, AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from src.api import comments as comment_routes
from tests.factories import DEFAULT_USER_ID, OTHER_USER_ID, build_comment


def _comment_create_payload(parent_comment_id: str | None = None) -> dict:
    payload = {"content": "This is a useful and constructive comment."}
    if parent_comment_id is not None:
        payload["parent_comment_id"] = parent_comment_id
    return payload


def test_get_user_id_from_header_returns_header_value():
    assert comment_routes.get_user_id_from_header(DEFAULT_USER_ID) == DEFAULT_USER_ID


def test_get_required_user_id_prefers_header_value():
    result = comment_routes.get_required_user_id(
        x_user_id=DEFAULT_USER_ID,
        token_payload={"internal_uid": OTHER_USER_ID, "sub": OTHER_USER_ID},
    )

    assert result == DEFAULT_USER_ID


def test_get_required_user_id_falls_back_to_token_payload():
    result = comment_routes.get_required_user_id(
        x_user_id=None,
        token_payload={"internal_uid": DEFAULT_USER_ID},
    )

    assert result == DEFAULT_USER_ID


def test_get_required_user_id_raises_401_when_no_user_id_available():
    with pytest.raises(HTTPException) as exc_info:
        comment_routes.get_required_user_id(x_user_id=None, token_payload={})

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "User ID not found in header or token"


@patch("src.api.comments.CommentService.get_comments_count_by_post", new_callable=AsyncMock)
def test_get_comments_count_success(mock_get_comments_count, client):
    post_id = uuid4()
    mock_get_comments_count.return_value = 6

    response = client.get(f"/forum/posts/{post_id}/comments/count")

    assert response.status_code == 200
    assert response.json() == {"post_id": str(post_id), "count": 6}
    mock_get_comments_count.assert_awaited_once_with(ANY, post_id)


@patch("src.api.comments.CommentService.create_comment", new_callable=AsyncMock)
def test_create_comment_success(mock_create_comment, client):
    post_id = uuid4()
    created_comment = build_comment(post_id=post_id, author_id=DEFAULT_USER_ID)
    mock_create_comment.return_value = created_comment

    response = client.post(
        f"/forum/posts/{post_id}/comments",
        json=_comment_create_payload(),
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["_id"] == str(created_comment.id)
    assert body["post_id"] == str(post_id)
    assert body["user_id"] == DEFAULT_USER_ID

    called_kwargs = mock_create_comment.await_args.kwargs
    assert called_kwargs["post_id"] == post_id
    assert called_kwargs["author_id"] == UUID(DEFAULT_USER_ID)
    assert called_kwargs["parent_comment_id"] is None


@patch("src.api.comments.CommentService.create_comment", new_callable=AsyncMock)
def test_create_comment_with_parent_comment_success(mock_create_comment, client):
    post_id = uuid4()
    parent_comment_id = uuid4()
    created_comment = build_comment(
        post_id=post_id,
        author_id=DEFAULT_USER_ID,
        parent_comment_id=parent_comment_id,
    )
    mock_create_comment.return_value = created_comment

    response = client.post(
        f"/forum/posts/{post_id}/comments",
        json=_comment_create_payload(parent_comment_id=str(parent_comment_id)),
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 201
    assert response.json()["parent_comment_id"] == str(parent_comment_id)

    called_kwargs = mock_create_comment.await_args.kwargs
    assert called_kwargs["parent_comment_id"] == parent_comment_id


@patch("src.api.comments.CommentService.create_comment", new_callable=AsyncMock)
def test_create_comment_returns_400_for_invalid_user_id(mock_create_comment, client):
    response = client.post(
        f"/forum/posts/{uuid4()}/comments",
        json=_comment_create_payload(),
        headers={"X-User-Id": "not-a-uuid"},
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Invalid User ID format")
    mock_create_comment.assert_not_awaited()


@patch("src.api.comments.CommentService.create_comment", new_callable=AsyncMock)
def test_create_comment_returns_400_for_invalid_parent_comment_id(mock_create_comment, client):
    response = client.post(
        f"/forum/posts/{uuid4()}/comments",
        json=_comment_create_payload(parent_comment_id="not-a-uuid"),
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Invalid parent_comment_id format")
    mock_create_comment.assert_not_awaited()


@patch("src.api.comments.CommentService.create_comment", new_callable=AsyncMock)
def test_create_comment_returns_404_when_post_or_parent_not_found(mock_create_comment, client):
    mock_create_comment.return_value = None

    response = client.post(
        f"/forum/posts/{uuid4()}/comments",
        json=_comment_create_payload(),
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Post or parent comment not found"


@patch("src.api.comments.CommentService.get_comments_by_post", new_callable=AsyncMock)
def test_get_comments_by_post_success(mock_get_comments_by_post, client):
    post_id = uuid4()
    first = build_comment(post_id=post_id, author_id=DEFAULT_USER_ID)
    second = build_comment(post_id=post_id, author_id=OTHER_USER_ID)
    mock_get_comments_by_post.return_value = [first, second]

    response = client.get(f"/forum/posts/{post_id}/comments", params={"skip": 1, "limit": 20})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["_id"] == str(first.id)
    assert body[1]["_id"] == str(second.id)
    mock_get_comments_by_post.assert_awaited_once_with(
        session=ANY,
        post_id=post_id,
        skip=1,
        limit=20,
    )


@patch("src.api.comments.CommentService.get_comments_tree", new_callable=AsyncMock)
def test_get_comments_tree_success(mock_get_comments_tree, client):
    post_id = uuid4()
    parent = build_comment(post_id=post_id, author_id=DEFAULT_USER_ID)
    reply = build_comment(post_id=post_id, author_id=OTHER_USER_ID, parent_comment_id=parent.id)
    mock_get_comments_tree.return_value = [
        {
            "comment": parent,
            "replies": [{"comment": reply, "replies": []}],
        }
    ]

    response = client.get(f"/forum/posts/{post_id}/comments/tree", params={"max_depth": 4})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["comment"]["_id"] == str(parent.id)
    assert body[0]["replies"][0]["comment"]["_id"] == str(reply.id)
    mock_get_comments_tree.assert_awaited_once_with(session=ANY, post_id=post_id, max_depth=4)


@patch("src.api.comments.CommentService.get_comment_by_id", new_callable=AsyncMock)
def test_get_comment_success(mock_get_comment_by_id, client):
    comment = build_comment(author_id=DEFAULT_USER_ID)
    mock_get_comment_by_id.return_value = comment

    response = client.get(f"/forum/comments/{comment.id}")

    assert response.status_code == 200
    assert response.json()["_id"] == str(comment.id)
    mock_get_comment_by_id.assert_awaited_once_with(session=ANY, comment_id=comment.id)


@patch("src.api.comments.CommentService.get_comment_by_id", new_callable=AsyncMock)
def test_get_comment_returns_404_when_missing(mock_get_comment_by_id, client):
    comment_id = uuid4()
    mock_get_comment_by_id.return_value = None

    response = client.get(f"/forum/comments/{comment_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == f"Comment {comment_id} not found"


@patch("src.api.comments.CommentService.get_comment_replies", new_callable=AsyncMock)
def test_get_comment_replies_success(mock_get_comment_replies, client):
    parent_comment_id = uuid4()
    reply = build_comment(parent_comment_id=parent_comment_id)
    mock_get_comment_replies.return_value = [reply]

    response = client.get(f"/forum/comments/{parent_comment_id}/replies", params={"skip": 0, "limit": 5})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["_id"] == str(reply.id)
    mock_get_comment_replies.assert_awaited_once_with(
        session=ANY,
        parent_comment_id=parent_comment_id,
        skip=0,
        limit=5,
    )


@patch("src.api.comments.CommentService.update_comment", new_callable=AsyncMock)
def test_update_comment_success(mock_update_comment, client):
    comment_id = uuid4()
    updated_comment = build_comment(comment_id=comment_id, author_id=DEFAULT_USER_ID, content="Updated")
    mock_update_comment.return_value = updated_comment

    response = client.patch(
        f"/forum/comments/{comment_id}",
        json={"content": "Updated"},
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 200
    assert response.json()["content"] == "Updated"
    mock_update_comment.assert_awaited_once_with(
        session=ANY,
        comment_id=comment_id,
        author_id=UUID(DEFAULT_USER_ID),
        content="Updated",
    )


@patch("src.api.comments.CommentService.update_comment", new_callable=AsyncMock)
def test_update_comment_returns_400_for_invalid_user_id(mock_update_comment, client):
    response = client.patch(
        f"/forum/comments/{uuid4()}",
        json={"content": "Updated"},
        headers={"X-User-Id": "not-a-uuid"},
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Invalid User ID format")
    mock_update_comment.assert_not_awaited()


@patch("src.api.comments.CommentService.update_comment", new_callable=AsyncMock)
def test_update_comment_returns_404_when_missing_or_forbidden(mock_update_comment, client):
    mock_update_comment.return_value = None

    response = client.patch(
        f"/forum/comments/{uuid4()}",
        json={"content": "Updated"},
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Comment not found or user is not the author"


@patch("src.api.comments.CommentService.delete_comment", new_callable=AsyncMock)
def test_delete_comment_success(mock_delete_comment, client):
    comment_id = uuid4()
    mock_delete_comment.return_value = True

    response = client.delete(f"/forum/comments/{comment_id}")

    assert response.status_code == 204
    mock_delete_comment.assert_awaited_once_with(
        session=ANY,
        comment_id=comment_id,
        author_id=UUID(DEFAULT_USER_ID),
    )


@patch("src.api.comments.CommentService.delete_comment", new_callable=AsyncMock)
def test_delete_comment_returns_400_for_invalid_user_id(mock_delete_comment, client):
    response = client.delete(
        f"/forum/comments/{uuid4()}",
        headers={"X-User-Id": "invalid-user"},
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Invalid User ID format")
    mock_delete_comment.assert_not_awaited()


@patch("src.api.comments.CommentService.delete_comment", new_callable=AsyncMock)
def test_delete_comment_returns_404_when_missing_or_forbidden(mock_delete_comment, client):
    mock_delete_comment.return_value = False

    response = client.delete(
        f"/forum/comments/{uuid4()}",
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Comment not found or user is not the author"


@patch("src.api.comments.LikeService.track_comment_like", new_callable=AsyncMock)
def test_like_comment_success(mock_track_comment_like, client):
    comment_id = uuid4()
    mock_track_comment_like.return_value = True

    response = client.post(
        f"/forum/comments/{comment_id}/like",
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Comment liked successfully"}
    mock_track_comment_like.assert_awaited_once_with(
        session=ANY,
        comment_id=comment_id,
        user_id=UUID(DEFAULT_USER_ID),
    )


@patch("src.api.comments.LikeService.track_comment_like", new_callable=AsyncMock)
def test_like_comment_returns_400_for_invalid_user_id(mock_track_comment_like, client):
    response = client.post(
        f"/forum/comments/{uuid4()}/like",
        headers={"X-User-Id": "invalid-user"},
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Invalid User ID format")
    mock_track_comment_like.assert_not_awaited()


@patch("src.api.comments.LikeService.track_comment_like", new_callable=AsyncMock)
def test_like_comment_returns_400_when_like_not_possible(mock_track_comment_like, client):
    mock_track_comment_like.return_value = False

    response = client.post(
        f"/forum/comments/{uuid4()}/like",
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Comment not found or already liked"


@patch("src.api.comments.LikeService.remove_comment_like", new_callable=AsyncMock)
def test_unlike_comment_success(mock_remove_comment_like, client):
    comment_id = uuid4()
    mock_remove_comment_like.return_value = True

    response = client.delete(
        f"/forum/comments/{comment_id}/like",
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Comment unliked successfully"}
    mock_remove_comment_like.assert_awaited_once_with(
        session=ANY,
        comment_id=comment_id,
        user_id=UUID(DEFAULT_USER_ID),
    )


@patch("src.api.comments.LikeService.remove_comment_like", new_callable=AsyncMock)
def test_unlike_comment_returns_400_for_invalid_user_id(mock_remove_comment_like, client):
    response = client.delete(
        f"/forum/comments/{uuid4()}/like",
        headers={"X-User-Id": "invalid-user"},
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Invalid User ID format")
    mock_remove_comment_like.assert_not_awaited()


@patch("src.api.comments.LikeService.remove_comment_like", new_callable=AsyncMock)
def test_unlike_comment_returns_400_when_unlike_not_possible(mock_remove_comment_like, client):
    mock_remove_comment_like.return_value = False

    response = client.delete(
        f"/forum/comments/{uuid4()}/like",
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Comment not found or not liked"


@patch("src.api.comments.LikeService.get_comment_likes_count", new_callable=AsyncMock)
def test_get_comment_likes_count_success(mock_get_comment_likes_count, client):
    comment_id = uuid4()
    mock_get_comment_likes_count.return_value = 9

    response = client.get(f"/forum/comments/{comment_id}/likes")

    assert response.status_code == 200
    assert response.json() == {"comment_id": str(comment_id), "likes_count": 9}


@patch("src.api.comments.LikeService.get_comment_likes_count", new_callable=AsyncMock)
def test_get_comment_likes_count_returns_404_when_comment_missing(mock_get_comment_likes_count, client):
    mock_get_comment_likes_count.return_value = None

    response = client.get(f"/forum/comments/{uuid4()}/likes")

    assert response.status_code == 404
    assert response.json()["detail"] == "Comment not found"


@patch("src.api.comments.LikeService.has_user_liked_comment", new_callable=AsyncMock)
def test_get_comment_like_status_success(mock_has_user_liked_comment, client):
    comment_id = uuid4()
    mock_has_user_liked_comment.return_value = True

    response = client.get(
        f"/forum/comments/{comment_id}/like/status",
        headers={"X-User-Id": DEFAULT_USER_ID},
    )

    assert response.status_code == 200
    assert response.json() == {"comment_id": str(comment_id), "liked": True}
    mock_has_user_liked_comment.assert_awaited_once_with(ANY, comment_id, UUID(DEFAULT_USER_ID))


@patch("src.api.comments.LikeService.has_user_liked_comment", new_callable=AsyncMock)
def test_get_comment_like_status_returns_400_for_invalid_user_id(mock_has_user_liked_comment, client):
    response = client.get(
        f"/forum/comments/{uuid4()}/like/status",
        headers={"X-User-Id": "invalid-user"},
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Invalid User ID format")
    mock_has_user_liked_comment.assert_not_awaited()
