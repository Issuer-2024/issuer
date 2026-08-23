import json
from unittest.mock import Mock, patch

from app.v2.external_request.sentiment.client import get_clova_sentiment
from app.v2.external_request.suggestion import RequestSuggestions


def test_given_sentiment_text_when_requested_then_clova_result_is_returned():
    # Given
    response = Mock(status_code=200)
    response.json.return_value = {"document": {"sentiment": "positive"}}

    # When
    with patch("app.v2.external_request.sentiment.client.requests.post", return_value=response) as post:
        result = get_clova_sentiment("오늘은 좋은 날이다")

    # Then
    assert result["document"]["sentiment"] == "positive"
    post.assert_called_once()
    assert json.loads(post.call_args.kwargs["data"]) == {"content": "오늘은 좋은 날이다"}


def test_given_suggestion_query_when_requested_then_google_suggestions_are_returned():
    # Given
    response = Mock()
    response.json.return_value = ["query", ["query one", "query two"]]

    # When
    with patch("app.v2.external_request.request_suggestions.requests.get", return_value=response):
        result = RequestSuggestions.get_suggestions("query")

    # Then
    assert result == ["query one", "query two"]
