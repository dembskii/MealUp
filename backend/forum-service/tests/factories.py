from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4

DEFAULT_USER_ID = "11111111-1111-1111-1111-111111111111"
OTHER_USER_ID = "22222222-2222-2222-2222-222222222222"


def _ensure_uuid(value: str | UUID) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def build_post(
    *,
    post_id: UUID | None = None,
    author_id: str | UUID = DEFAULT_USER_ID,
    title: str = "Sample forum post",
    content: str = "Sample forum post content used for endpoint testing.",
    tags: list[str] | None = None,
    images: list[str] | None = None,
    linked_recipes: list[str] | None = None,
    linked_workouts: list[str] | None = None,
    total_likes: int = 3,
    views_count: int = 8,
    trending_coefficient: float = 1.2,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> SimpleNamespace:
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=post_id or uuid4(),
        author_id=_ensure_uuid(author_id),
        title=title,
        content=content,
        tags=tags if tags is not None else ["fitness", "mealup"],
        images=images if images is not None else ["https://example.com/post.jpg"],
        linked_recipes=linked_recipes if linked_recipes is not None else [str(uuid4())],
        linked_workouts=linked_workouts if linked_workouts is not None else [str(uuid4())],
        total_likes=total_likes,
        views_count=views_count,
        trending_coefficient=trending_coefficient,
        created_at=created_at or now,
        updated_at=updated_at or now,
    )


def build_comment(
    *,
    comment_id: UUID | None = None,
    post_id: UUID | None = None,
    author_id: str | UUID = DEFAULT_USER_ID,
    content: str = "Great post, thanks for sharing!",
    parent_comment_id: str | UUID | None = None,
    total_likes: int = 2,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> SimpleNamespace:
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=comment_id or uuid4(),
        post_id=post_id or uuid4(),
        author_id=_ensure_uuid(author_id),
        content=content,
        parent_comment_id=_ensure_uuid(parent_comment_id) if parent_comment_id else None,
        total_likes=total_likes,
        created_at=created_at or now,
        updated_at=updated_at or now,
    )


def build_post_search_result(*, post_id: str | None = None, author_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {
        "id": post_id or str(uuid4()),
        "title": "Protein rich breakfast",
        "content": "Try oats with greek yogurt and fruit for high protein breakfast.",
        "author_id": author_id,
        "author_name": "Test User",
        "tags": ["nutrition", "protein"],
        "images": ["https://example.com/meal.jpg"],
        "linked_recipes": [str(uuid4())],
        "linked_workouts": [str(uuid4())],
        "total_likes": 11,
        "views_count": 72,
        "comments_count": 4,
        "trending_coefficient": 2.5,
        "created_at": now,
        "updated_at": now,
        "relevance_score": 0.98,
        "result_type": "post",
    }


def build_search_response(
    *,
    query: str = "protein",
    category: str = "all",
    posts: list[dict[str, Any]] | None = None,
    recipes: list[dict[str, Any]] | None = None,
    workouts: list[dict[str, Any]] | None = None,
    authors: list[dict[str, Any]] | None = None,
    has_more: bool = False,
) -> dict[str, Any]:
    posts_data = posts or []
    recipes_data = recipes or []
    workouts_data = workouts or []
    authors_data = authors or []

    return {
        "query": query,
        "category": category,
        "total_results": len(posts_data) + len(recipes_data) + len(workouts_data) + len(authors_data),
        "posts": posts_data,
        "recipes": recipes_data,
        "workouts": workouts_data,
        "authors": authors_data,
        "has_more": has_more,
    }


def build_ai_response() -> dict[str, Any]:
    return {
        "answer": "Focus on balanced meals with enough protein and hydration.",
        "sources": [{"id": str(uuid4()), "title": "Meal planning basics"}],
    }
