import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import httpx

from src.services import embedding_service as embedding
from src.services import rag_service as rag
from src.services.search_service import SearchService
from src.validators.search import SearchCategory, SearchQuery, SearchSortBy
from tests.unit.fakes import (
    FakeAsyncSession,
    FakeHttpResponse,
    FakeResult,
    build_http_client_factory,
)


def run(coro):
    return asyncio.run(coro)


class _EmbeddingsClient:
    def __init__(self, vector=None, error=None):
        self._vector = vector or [0.1, 0.2]
        self._error = error

    async def create(self, **kwargs):
        if self._error:
            raise self._error
        return SimpleNamespace(data=[SimpleNamespace(embedding=self._vector)])


def _build_post(title="Title", content="Content", tags=None):
    return SimpleNamespace(
        id=uuid4(),
        title=title,
        content=content,
        tags=tags if tags is not None else ["fitness"],
    )


def test_build_post_text_joins_available_fields():
    post = _build_post(title="A", content="B", tags=["x", "y"])

    text = embedding.build_post_text(post)

    assert "Title: A" in text
    assert "Content: B" in text
    assert "Tags: x, y" in text


def test_generate_embedding_returns_none_for_blank_input():
    assert run(embedding.generate_embedding("   ")) is None


def test_generate_embedding_returns_vector(monkeypatch):
    fake_client = SimpleNamespace(embeddings=_EmbeddingsClient(vector=[0.9, 0.8]))
    monkeypatch.setattr(embedding, "client", fake_client)

    result = run(embedding.generate_embedding("hello"))

    assert result == [0.9, 0.8]


def test_generate_embedding_handles_client_error(monkeypatch):
    fake_client = SimpleNamespace(embeddings=_EmbeddingsClient(error=RuntimeError("boom")))
    monkeypatch.setattr(embedding, "client", fake_client)

    assert run(embedding.generate_embedding("hello")) is None


def test_embed_post_saves_embedding_when_generated(monkeypatch):
    session = FakeAsyncSession()
    post = _build_post()

    async def _fake_generate(_text):
        return [0.3, 0.4]

    monkeypatch.setattr(embedding, "generate_embedding", _fake_generate)

    result = run(embedding.embed_post(session, post))

    assert result == [0.3, 0.4]
    assert post.embedding == [0.3, 0.4]
    assert session.commits == 1
    assert session.added[-1] is post


def test_embed_post_rolls_back_on_error(monkeypatch):
    session = FakeAsyncSession()
    post = _build_post()

    async def _fake_generate(_text):
        raise RuntimeError("embed error")

    monkeypatch.setattr(embedding, "generate_embedding", _fake_generate)

    result = run(embedding.embed_post(session, post))

    assert result is None
    assert session.rollbacks == 1


def test_vector_search_returns_empty_without_query_embedding(monkeypatch):
    async def _no_embedding(_query):
        return None

    monkeypatch.setattr(rag, "generate_embedding", _no_embedding)

    result = run(rag.vector_search(FakeAsyncSession(), "q"))

    assert result == []


def test_vector_search_returns_posts(monkeypatch):
    post = _build_post("Found", "Body")
    session = FakeAsyncSession(exec_plan=[FakeResult(all_values=[post])])

    async def _embedding(_query):
        return [0.1] * 1536

    monkeypatch.setattr(rag, "generate_embedding", _embedding)

    result = run(rag.vector_search(session, "fitness", top_k=3))

    assert len(result) == 1
    assert result[0].title == "Found"


def test_ask_returns_no_sources_message(monkeypatch):
    async def _vector_search(*args, **kwargs):
        return []

    monkeypatch.setattr(rag, "vector_search", _vector_search)

    result = run(rag.ask(FakeAsyncSession(), "question"))

    assert "No relevant posts" in result["answer"]
    assert result["sources"] == []


def test_ask_returns_answer_and_sources(monkeypatch):
    post = _build_post("Source title", "Source content")

    async def _vector_search(*args, **kwargs):
        return [post]

    class _ChatCreate:
        async def create(self, **kwargs):
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="Use [1]"))]
            )

    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=_ChatCreate()))
    monkeypatch.setattr(rag, "vector_search", _vector_search)
    monkeypatch.setattr(rag, "client", fake_client)

    result = run(rag.ask(FakeAsyncSession(), "question"))

    assert result["answer"] == "Use [1]"
    assert result["sources"][0]["title"] == "Source title"


def test_search_aggregates_all_categories(monkeypatch):
    now = datetime.now(timezone.utc)

    async def _posts(**kwargs):
        return [
            {
                "id": "p1",
                "title": "Post",
                "content": "Content",
                "author_id": str(uuid4()),
                "created_at": now,
            }
        ]

    async def _authors(**kwargs):
        return [{"id": "a1", "name": "Jan"}]

    async def _recipes(**kwargs):
        return [{"id": "r1", "name": "Recipe"}]

    async def _workouts(**kwargs):
        return [{"id": "w1", "name": "Workout"}]

    monkeypatch.setattr(SearchService, "_search_posts", _posts)
    monkeypatch.setattr(SearchService, "_search_authors", _authors)
    monkeypatch.setattr(SearchService, "_search_recipes", _recipes)
    monkeypatch.setattr(SearchService, "_search_workouts", _workouts)

    query = SearchQuery(query="fit", category=SearchCategory.ALL, limit=1)
    result = run(SearchService.search(FakeAsyncSession(), query, auth_token="Bearer x"))

    assert result.total_results == 4
    assert result.has_more is True


def test_search_returns_empty_response_on_internal_error(monkeypatch):
    async def _broken(**kwargs):
        raise RuntimeError("down")

    monkeypatch.setattr(SearchService, "_search_posts", _broken)

    query = SearchQuery(query="fit", category=SearchCategory.POSTS)
    result = run(SearchService.search(FakeAsyncSession(), query))

    assert result.total_results == 0
    assert result.posts == []


def test_search_posts_maps_database_rows_to_schema():
    now = datetime.now(timezone.utc)
    post = SimpleNamespace(
        id=uuid4(),
        title="Protein plan",
        content="x" * 520,
        author_id=uuid4(),
        tags=["protein"],
        images=["img"],
        linked_recipes=["r"],
        linked_workouts=["w"],
        total_likes=5,
        views_count=20,
        trending_coefficient=1.4,
        created_at=now,
        updated_at=now,
    )
    session = FakeAsyncSession(
        exec_plan=[
            FakeResult(all_values=[post]),
            FakeResult(first=7),
        ]
    )

    results = run(
        SearchService._search_posts(
            session=session,
            query="protein",
            tags=["protein"],
            author_id="not-a-uuid",
            sort_by=SearchSortBy.NEWEST,
            skip=0,
            limit=10,
        )
    )

    assert len(results) == 1
    assert results[0].comments_count == 7
    assert len(results[0].content) == 500


def test_search_posts_returns_empty_on_error():
    session = FakeAsyncSession(exec_plan=[RuntimeError("db error")])

    assert run(SearchService._search_posts(session=session, query="x")) == []


def test_search_authors_success(monkeypatch):
    payload = {
        "items": [
            {"uid": str(uuid4()), "first_name": "Jan", "last_name": "Kowalski", "username": "jk"}
        ]
    }
    response = FakeHttpResponse(200, payload)
    monkeypatch.setattr(
        "src.services.search_service.httpx.AsyncClient",
        build_http_client_factory(response=response),
    )

    session = FakeAsyncSession(exec_plan=[FakeResult(first=(2, 11))])

    result = run(SearchService._search_authors(session=session, query="jan"))

    assert len(result) == 1
    assert result[0].name == "Jan Kowalski"
    assert result[0].posts_count == 2


def test_search_authors_handles_non_200(monkeypatch):
    monkeypatch.setattr(
        "src.services.search_service.httpx.AsyncClient",
        build_http_client_factory(response=FakeHttpResponse(503, {})),
    )

    result = run(SearchService._search_authors(session=FakeAsyncSession(), query="jan"))

    assert result == []


def test_search_authors_handles_timeout(monkeypatch):
    monkeypatch.setattr(
        "src.services.search_service.httpx.AsyncClient",
        build_http_client_factory(error=httpx.TimeoutException("timeout")),
    )

    result = run(SearchService._search_authors(session=FakeAsyncSession(), query="jan"))

    assert result == []


def test_search_recipes_success(monkeypatch):
    payload = [
        {
            "_id": "r1",
            "name": "Recipe",
            "prepare_instruction": "A" * 300,
            "author_id": "u1",
            "time_to_prepare": 120,
            "tags": ["quick"],
            "images": ["img"],
        }
    ]
    monkeypatch.setattr(
        "src.services.search_service.httpx.AsyncClient",
        build_http_client_factory(response=FakeHttpResponse(200, payload)),
    )

    result = run(SearchService._search_recipes(query="omlet", tags=["quick"], auth_token="Bearer t"))

    assert len(result) == 1
    assert result[0].id == "r1"
    assert len(result[0].description) == 200


def test_search_recipes_timeout_returns_empty(monkeypatch):
    monkeypatch.setattr(
        "src.services.search_service.httpx.AsyncClient",
        build_http_client_factory(error=httpx.TimeoutException("timeout")),
    )

    assert run(SearchService._search_recipes(query="x")) == []


def test_search_workouts_success(monkeypatch):
    payload = [
        {
            "_id": "w1",
            "name": "Workout",
            "description": "desc",
            "advancement": "beginner",
            "category": "strength",
            "tags": ["legs"],
        }
    ]
    monkeypatch.setattr(
        "src.services.search_service.httpx.AsyncClient",
        build_http_client_factory(response=FakeHttpResponse(200, payload)),
    )

    result = run(SearchService._search_workouts(query="legs", auth_token="Bearer t"))

    assert len(result) == 1
    assert result[0].id == "w1"
    assert result[0].difficulty == "beginner"


def test_search_workouts_timeout_returns_empty(monkeypatch):
    monkeypatch.setattr(
        "src.services.search_service.httpx.AsyncClient",
        build_http_client_factory(error=httpx.TimeoutException("timeout")),
    )

    assert run(SearchService._search_workouts(query="x")) == []


def test_get_search_suggestions_with_titles(monkeypatch):
    async def _popular_tags(**kwargs):
        return [SimpleNamespace(tag="fit", count=10)]

    monkeypatch.setattr(SearchService, "get_popular_tags", _popular_tags)
    session = FakeAsyncSession(exec_plan=[FakeResult(all_values=[("fitness",), ("fit meal",)])])

    result = run(SearchService.get_search_suggestions(session=session, query="fi", limit=5))

    assert result.suggestions == ["fitness", "fit meal"]
    assert result.tags[0].tag == "fit"


def test_get_search_suggestions_short_query_skips_title_lookup(monkeypatch):
    async def _popular_tags(**kwargs):
        return []

    monkeypatch.setattr(SearchService, "get_popular_tags", _popular_tags)
    session = FakeAsyncSession()

    result = run(SearchService.get_search_suggestions(session=session, query="f", limit=5))

    assert result.suggestions == []
    assert len(session.exec_calls) == 0


def test_get_popular_tags_with_query_returns_rows():
    session = FakeAsyncSession(exec_plan=[FakeResult(all_values=[("fit", 8), ("meal", 4)])])

    result = run(SearchService.get_popular_tags(session=session, query="fi", limit=2))

    assert [x.tag for x in result] == ["fit", "meal"]


def test_get_popular_tags_on_error_returns_empty():
    session = FakeAsyncSession(exec_plan=[RuntimeError("db")])

    assert run(SearchService.get_popular_tags(session=session, query=None)) == []


def test_search_by_tag_maps_results_and_comment_counts():
    now = datetime.now(timezone.utc)
    rows = [
        (
            "p1",
            "Title",
            "Body",
            "a1",
            ["fit"],
            ["img"],
            5,
            9,
            1.1,
            now,
            now,
            ["r1"],
            ["w1"],
        )
    ]
    session = FakeAsyncSession(
        exec_plan=[
            FakeResult(all_values=rows),
            FakeResult(scalar=3),
        ]
    )

    result = run(
        SearchService.search_by_tag(
            session=session,
            tag="fit",
            sort_by=SearchSortBy.MOST_LIKED,
            skip=0,
            limit=10,
        )
    )

    assert len(result) == 1
    assert result[0].comments_count == 3
    assert result[0].linked_recipes == ["r1"]


def test_search_by_tag_returns_empty_on_error():
    session = FakeAsyncSession(exec_plan=[RuntimeError("db")])

    assert run(SearchService.search_by_tag(session=session, tag="fit")) == []
