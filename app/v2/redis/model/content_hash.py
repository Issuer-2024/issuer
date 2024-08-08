from typing import List, Dict, Any

from redis_om import Field, JsonModel


class ContentHash(JsonModel):
    keyword: str = Field(index=True)
    created_at: str = Field(index=True)
    keyword_trend_data: List[Dict[str, Any]]
    keyword_suggestions_data: List[Dict[str, Any]]
    public_opinion_activity_data: Dict[str, Any]
    public_opinion_word_frequency: List[Any]
    table_of_contents: List[Dict[str, Any]]
    body: List[Dict[str, Any]]
    trend_public_opinion: Any
    table_of_public_opinion: Any
