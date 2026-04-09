from unittest.mock import ANY, AsyncMock, patch

from src.api import search as search_routes
from tests.factories import build_post_search_result, build_search_response


def test_get_authorization_header_returns_header_value():
    token = "Bearer test-token"
    assert search_routes.get_authorization_header(token) == token


def test_get_authorization_header_allows_none():
    assert search_routes.get_authorization_header(None) is None


@patch("src.api.search.SearchService.search", new_callable=AsyncMock)
def test_search_get_success(mock_search, client):
    mock_search.return_value = build_search_response(
        query="protein",
        posts=[build_post_search_result()],
    )

    response = client.get(
        "/forum/search",
        params={"q": "protein", "category": "all", "skip": 0, "limit": 20},
        headers={"Authorization": "Bearer forwarded-token"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "protein"
    assert body["total_results"] == 1

    called_kwargs = mock_search.await_args.kwargs
    assert called_kwargs["session"] is not None
    assert called_kwargs["search_query"].query == "protein"
    assert called_kwargs["auth_token"] == "Bearer forwarded-token"


@patch("src.api.search.SearchService.search", new_callable=AsyncMock)
def test_search_get_returns_400_for_validation_error(mock_search, client):
    mock_search.side_effect = ValueError("Invalid search query")

    response = client.get("/forum/search", params={"q": "protein"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid search query"


@patch("src.api.search.SearchService.search", new_callable=AsyncMock)
def test_search_get_returns_500_for_unexpected_error(mock_search, client):
    mock_search.side_effect = RuntimeError("search backend down")

    response = client.get("/forum/search", params={"q": "protein"})

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to perform search"


def test_search_get_returns_422_when_required_query_missing(client):
    response = client.get("/forum/search")

    assert response.status_code == 422


@patch("src.api.search.SearchService.search", new_callable=AsyncMock)
def test_search_post_success(mock_search, client):
    mock_search.return_value = build_search_response(
        query="leg day",
        posts=[build_post_search_result()],
    )

    response = client.post(
        "/forum/search",
        json={"query": "leg day", "category": "all", "skip": 0, "limit": 10},
        headers={"Authorization": "Bearer forwarded-token"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "leg day"
    assert body["total_results"] == 1

    called_kwargs = mock_search.await_args.kwargs
    assert called_kwargs["search_query"].query == "leg day"
    assert called_kwargs["auth_token"] == "Bearer forwarded-token"


@patch("src.api.search.SearchService.search", new_callable=AsyncMock)
def test_search_post_returns_400_for_validation_error(mock_search, client):
    mock_search.side_effect = ValueError("Body validation failed")

    response = client.post(
        "/forum/search",
        json={"query": "leg day", "category": "all", "skip": 0, "limit": 10},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Body validation failed"


@patch("src.api.search.SearchService.search", new_callable=AsyncMock)
def test_search_post_returns_500_for_unexpected_error(mock_search, client):
    mock_search.side_effect = RuntimeError("search backend down")

    response = client.post(
        "/forum/search",
        json={"query": "leg day", "category": "all", "skip": 0, "limit": 10},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to perform search"


@patch("src.api.search.SearchService.get_search_suggestions", new_callable=AsyncMock)
def test_get_search_suggestions_success(mock_get_search_suggestions, client):
    mock_get_search_suggestions.return_value = {
        "query": "fi",
        "suggestions": ["fitness", "fiber"],
        "tags": [{"tag": "fitness", "count": 10}],
    }

    response = client.get("/forum/search/suggestions", params={"q": "fi", "limit": 5})

    assert response.status_code == 200
    assert response.json()["suggestions"] == ["fitness", "fiber"]
    mock_get_search_suggestions.assert_awaited_once_with(session=ANY, query="fi", limit=5)


@patch("src.api.search.SearchService.get_search_suggestions", new_callable=AsyncMock)
def test_get_search_suggestions_returns_500_on_service_error(mock_get_search_suggestions, client):
    mock_get_search_suggestions.side_effect = RuntimeError("cannot fetch suggestions")

    response = client.get("/forum/search/suggestions", params={"q": "fi"})

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to get suggestions"


@patch("src.api.search.SearchService.get_popular_tags", new_callable=AsyncMock)
def test_get_popular_tags_success(mock_get_popular_tags, client):
    mock_get_popular_tags.return_value = [{"tag": "fitness", "count": 20}]

    response = client.get("/forum/search/tags", params={"q": "fit", "limit": 10})

    assert response.status_code == 200
    assert response.json() == [{"tag": "fitness", "count": 20}]
    mock_get_popular_tags.assert_awaited_once_with(session=ANY, query="fit", limit=10)


@patch("src.api.search.SearchService.get_popular_tags", new_callable=AsyncMock)
def test_get_popular_tags_returns_500_on_service_error(mock_get_popular_tags, client):
    mock_get_popular_tags.side_effect = RuntimeError("cannot fetch tags")

    response = client.get("/forum/search/tags")

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to get popular tags"


@patch("src.api.search.SearchService.search_by_tag", new_callable=AsyncMock)
def test_search_by_tag_success(mock_search_by_tag, client):
    result = build_post_search_result()
    mock_search_by_tag.return_value = [result]

    response = client.get(
        "/forum/search/by-tag/fitness",
        params={"sort_by": "newest", "skip": 1, "limit": 5},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == result["id"]

    mock_search_by_tag.assert_awaited_once_with(
        session=ANY,
        tag="fitness",
        sort_by=ANY,
        skip=1,
        limit=5,
    )


@patch("src.api.search.SearchService.search_by_tag", new_callable=AsyncMock)
def test_search_by_tag_returns_400_for_blank_tag(mock_search_by_tag, client):
    response = client.get("/forum/search/by-tag/%20%20")

    assert response.status_code == 400
    assert response.json()["detail"] == "Tag cannot be empty"
    mock_search_by_tag.assert_not_awaited()


@patch("src.api.search.SearchService.search_by_tag", new_callable=AsyncMock)
def test_search_by_tag_returns_500_on_service_error(mock_search_by_tag, client):
    mock_search_by_tag.side_effect = RuntimeError("search failed")

    response = client.get("/forum/search/by-tag/fitness")

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to search by tag"


@patch("src.api.search.SearchService._search_posts", new_callable=AsyncMock)
def test_search_posts_only_success(mock_search_posts_only, client):
    result = build_post_search_result()
    mock_search_posts_only.return_value = [result]

    response = client.get(
        "/forum/search/posts",
        params={"q": "protein", "sort_by": "relevance", "skip": 0, "limit": 10},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == result["id"]

    called_kwargs = mock_search_posts_only.await_args.kwargs
    assert called_kwargs["session"] is not None
    assert called_kwargs["query"] == "protein"
    assert called_kwargs["skip"] == 0
    assert called_kwargs["limit"] == 10


@patch("src.api.search.SearchService._search_posts", new_callable=AsyncMock)
def test_search_posts_only_returns_400_for_validation_error(mock_search_posts_only, client):
    mock_search_posts_only.side_effect = ValueError("Invalid author_id")

    response = client.get("/forum/search/posts", params={"q": "protein"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid author_id"


@patch("src.api.search.SearchService._search_posts", new_callable=AsyncMock)
def test_search_posts_only_returns_500_for_unexpected_error(mock_search_posts_only, client):
    mock_search_posts_only.side_effect = RuntimeError("search failed")

    response = client.get("/forum/search/posts", params={"q": "protein"})

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to search posts"
