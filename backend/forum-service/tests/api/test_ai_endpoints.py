from unittest.mock import ANY, AsyncMock, patch

from tests.factories import build_ai_response


@patch("src.api.ai.ask", new_callable=AsyncMock)
def test_rag_query_success(mock_ask, client):
    mock_ask.return_value = build_ai_response()

    response = client.post(
        "/forum/ai/ask",
        json={"question": "What should I eat after a hard workout?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"]
    assert len(body["sources"]) == 1
    mock_ask.assert_awaited_once_with(ANY, "What should I eat after a hard workout?", 5)


@patch("src.api.ai.ask", new_callable=AsyncMock)
def test_rag_query_success_when_no_sources_found(mock_ask, client):
    mock_ask.return_value = {
        "answer": "No relevant posts found to answer your question.",
        "sources": [],
    }

    response = client.post(
        "/forum/ai/ask",
        json={"question": "Very niche topic", "top_k": 3},
    )

    assert response.status_code == 200
    assert response.json()["sources"] == []
    mock_ask.assert_awaited_once_with(ANY, "Very niche topic", 3)


@patch("src.api.ai.ask", new_callable=AsyncMock)
def test_rag_query_returns_400_for_blank_question(mock_ask, client):
    response = client.post(
        "/forum/ai/ask",
        json={"question": "   ", "top_k": 3},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Question cannot be empty"
    mock_ask.assert_not_awaited()


@patch("src.api.ai.ask", new_callable=AsyncMock)
def test_rag_query_returns_400_for_validation_error(mock_ask, client):
    mock_ask.side_effect = ValueError("Unsupported query")

    response = client.post(
        "/forum/ai/ask",
        json={"question": "Give me advice about carbs and proteins"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid input: Unsupported query"


@patch("src.api.ai.ask", new_callable=AsyncMock)
def test_rag_query_returns_503_on_connection_error(mock_ask, client):
    mock_ask.side_effect = ConnectionError("upstream timeout")

    response = client.post(
        "/forum/ai/ask",
        json={"question": "How to build endurance safely?"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "AI service temporarily unavailable"


@patch("src.api.ai.ask", new_callable=AsyncMock)
def test_rag_query_returns_500_on_unexpected_error(mock_ask, client):
    mock_ask.side_effect = RuntimeError("unexpected failure")

    response = client.post(
        "/forum/ai/ask",
        json={"question": "How to improve sleep for recovery?"},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"
