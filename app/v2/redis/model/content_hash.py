from typing import List, Dict, Any

from redis_om import Field, JsonModel


class ContentHash(JsonModel):
    keyword: str = Field(index=True)
    created_at: str = Field(index=True)
    keyword_trend_data: List[Dict[str, Any]]
    keyword_suggestions_data: List[Dict[str, Any]]
    public_opinion_sentiment: Any
    public_opinion_word_frequency: Any
    table_of_contents: List[Dict[str, Any]]
    body: List[Dict[str, Any]]
    table_of_public_opinion: Any
    public_opinion_trend: Any
    public_opinion_summary: Any