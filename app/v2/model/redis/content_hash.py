from redis_om import HashModel


class ContentHash(HashModel):
    keyword: str
    created_at: str
    keyword_trend_data: list
    table_of_contents: list
    body: list
