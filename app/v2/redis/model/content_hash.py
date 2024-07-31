from typing import List, Dict, Any

from redis_om import HashModel, Field, JsonModel


class ContentHash(JsonModel):
    keyword: str = Field(index=True)
    created_at: str
    keyword_trend_data: List[Dict[str, Any]]
    table_of_contents: List[Dict[str, Any]]
    body: List[Dict[str, Any]]
